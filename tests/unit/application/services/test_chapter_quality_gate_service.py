from datetime import datetime
from unittest.mock import Mock

from application.audit.dtos.chapter_review_dto import ChapterReviewDTO
from application.core.services.chapter_quality_gate_service import ChapterQualityGateService
from domain.novel.entities.chapter import Chapter, ChapterStatus
from domain.novel.value_objects.novel_id import NovelId
from domain.structure.story_node import NodeType, StoryNode, StoryTree


def _chapter(content: str, status: ChapterStatus = ChapterStatus.DRAFT) -> Chapter:
    return Chapter(
        id="chapter-1",
        novel_id=NovelId("novel-1"),
        number=1,
        title="第一章",
        content=content,
        status=status,
    )


def _review(status: str) -> ChapterReviewDTO:
    now = datetime.utcnow()
    return ChapterReviewDTO(status=status, memo="", created_at=now, updated_at=now)


def _service(chapter: Chapter, review_status: str = "draft") -> ChapterQualityGateService:
    chapter_service = Mock()
    chapter_service.get_chapter_by_novel_and_number.return_value = chapter
    chapter_service.get_chapter_review.return_value = _review(review_status)
    return ChapterQualityGateService(chapter_service)


def test_empty_chapter_is_blocked():
    gate = _service(_chapter("")).evaluate("novel-1", 1)

    assert gate.gate_status == "blocked"
    assert gate.can_enter_next is False
    assert any(issue.code == "empty_chapter" for issue in gate.issues)


def test_short_chapter_needs_revision():
    gate = _service(_chapter("短章结尾。" * 20)).evaluate("novel-1", 1)

    assert gate.gate_status == "needs_revision"
    assert gate.can_lock is True
    assert any(issue.code == "too_short" for issue in gate.issues)


def test_completed_locked_chapter_passes():
    content = "这是一个完整段落。" * 500
    gate = _service(_chapter(content, ChapterStatus.COMPLETED), "locked").evaluate("novel-1", 1)

    assert gate.gate_status == "pass"
    assert gate.can_enter_next is True
    assert gate.issues == []


def test_revision_required_blocks_next_chapter():
    content = "这是一个完整段落。" * 500
    gate = _service(_chapter(content), "revision_required").evaluate("novel-1", 1)

    assert gate.gate_status == "blocked"
    assert gate.can_enter_next is False
    assert any(issue.code == "revision_required" for issue in gate.issues)


def test_mark_review_pending_does_not_enter_next_context():
    chapter = _chapter("完整段落。" * 500)
    chapter_service = Mock()
    chapter_service.get_chapter_by_novel_and_number.return_value = chapter
    chapter_service.get_chapter_review.side_effect = [
        _review("review_pending"),
    ]
    service = ChapterQualityGateService(chapter_service)

    gate = service.mark_review_pending("novel-1", 1)

    chapter_service.save_chapter_review.assert_called_once()
    assert gate.review_status == "review_pending"
    assert gate.can_enter_next is False


def test_mark_synced_enters_next_context():
    chapter = _chapter("完整段落。" * 500, ChapterStatus.COMPLETED)
    chapter_service = Mock()
    chapter_service.get_chapter_by_novel_and_number.return_value = chapter
    chapter_service.get_chapter_review.side_effect = [
        _review("synced"),
    ]
    service = ChapterQualityGateService(chapter_service)

    gate = service.mark_synced("novel-1", 1)

    chapter_service.save_chapter_review.assert_called_once()
    assert gate.review_status == "synced"
    assert gate.can_enter_next is True


def test_preflight_replaces_generic_outline_with_authority_lock():
    chapter = _chapter("完整段落。" * 500)
    chapter.outline = "主角发现遗迹真正入口，并在章末做出进入决定。"
    service = _service(chapter)

    preflight = service.preflight(
        "novel-1",
        1,
        outline="承接前情，推进主线与人物节拍；保持人设与叙事节奏一致。",
    )

    assert preflight.outline_source == "chapters.outline"
    assert "遗迹真正入口" in preflight.selected_outline
    assert any("权威大纲" in item for item in preflight.authority_lock)


def test_preflight_prefers_story_node_blueprint_outline_and_tension():
    chapter = _chapter("完整段落。" * 500)
    chapter.outline = "旧章节表大纲"
    story_repo = Mock()
    story_repo.get_tree_sync.return_value = StoryTree(
        novel_id="novel-1",
        nodes=[
            StoryNode(
                id="chapter-node-1",
                novel_id="novel-1",
                node_type=NodeType.CHAPTER,
                number=1,
                title="第一章",
                order_index=1,
                outline="蓝图大纲",
                metadata={
                    "blueprint": {
                        "outline": "蓝图大纲：李维抵达遗迹入口，并留下下一章开门钩子。",
                        "narrative_function": "setup",
                        "target_tension": 3,
                        "tension_phase": "铺垫",
                        "must_happen": ["李维确认入口坐标"],
                        "handoff_to_next": "下一章从开门前的异常读数接起",
                    }
                },
            )
        ],
    )
    chapter_service = Mock()
    chapter_service.get_chapter_by_novel_and_number.return_value = chapter
    chapter_service.get_chapter_review.return_value = _review("draft")
    service = ChapterQualityGateService(chapter_service, story_repo)

    preflight = service.preflight("novel-1", 1, outline="承接前情，推进主线，保持人设与叙事节奏一致。")

    assert preflight.outline_source == "story_nodes.blueprint"
    assert "李维抵达遗迹入口" in preflight.selected_outline
    assert any("3/10" in item for item in preflight.authority_lock)
    assert any("setup" in item for item in preflight.authority_lock)
