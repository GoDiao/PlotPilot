"""Chapter quality gate service.

This service creates the product-level chapter gate used by the trustworthy
creation loop. It is deterministic and cheap: deeper LLM diagnostics can feed
the same gate later, but this baseline already prevents empty/truncated drafts
from being treated as ready for the next chapter.
"""
from __future__ import annotations

import re
from typing import Optional, Any

from application.core.dtos.chapter_quality_gate_dto import (
    ChapterGateIssueDTO,
    ChapterIssueTaskDTO,
    ChapterPreflightDTO,
    ChapterQualityGateDTO,
)
from application.core.services.chapter_service import ChapterService


LOCKED_REVIEW_STATUS = "locked"
SYNCED_REVIEW_STATUS = "synced"
REVISION_REQUIRED_STATUS = "revision_required"
REVIEW_PENDING_STATUS = "review_pending"


class ChapterQualityGateService:
    def __init__(self, chapter_service: ChapterService, story_node_repository: Any = None):
        self.chapter_service = chapter_service
        self.story_node_repository = story_node_repository

    def evaluate(self, novel_id: str, chapter_number: int) -> ChapterQualityGateDTO:
        chapter = self.chapter_service.get_chapter_by_novel_and_number(novel_id, chapter_number)
        if chapter is None:
            raise ValueError(f"Chapter not found: {novel_id}/chapter-{chapter_number}")

        review = self.chapter_service.get_chapter_review(novel_id, chapter_number)
        content = chapter.content or ""
        word_count = len(content.strip())
        review_status = review.status or "draft"
        issues: list[ChapterGateIssueDTO] = []
        suggestions: list[str] = []

        if word_count == 0:
            issues.append(ChapterGateIssueDTO(
                code="empty_chapter",
                severity="blocker",
                message="章节正文为空，不能进入下一章。",
                action="先生成或撰写本章正文。",
            ))
        elif word_count < 800:
            issues.append(ChapterGateIssueDTO(
                code="too_short",
                severity="major",
                message=f"章节仅 {word_count} 字，可能只是片段草稿。",
                action="继续扩写或确认这是短章节。",
            ))

        ending_issue = self._detect_open_ending(content)
        if ending_issue:
            issues.append(ending_issue)

        if review_status in {"draft", REVIEW_PENDING_STATUS, "reviewed"}:
            suggestions.append("完成章节审稿后再锁定；锁定后才建议作为后续强上下文。")
        if review_status == REVISION_REQUIRED_STATUS:
            issues.append(ChapterGateIssueDTO(
                code="revision_required",
                severity="blocker",
                message="章节被标记为需修订，不能进入下一章。",
                action="处理审稿问题或重新生成。",
            ))

        blocker_count = sum(1 for issue in issues if issue.severity == "blocker")
        major_count = sum(1 for issue in issues if issue.severity == "major")
        can_lock = blocker_count == 0 and word_count > 0
        can_enter_next = review_status in {LOCKED_REVIEW_STATUS, SYNCED_REVIEW_STATUS, "approved"} and blocker_count == 0
        if blocker_count:
            gate_status = "blocked"
        elif major_count:
            gate_status = "needs_revision"
        elif can_enter_next:
            gate_status = "pass"
        else:
            gate_status = "review_pending"

        chapter_status = chapter.status.value if hasattr(chapter.status, "value") else str(chapter.status)

        return ChapterQualityGateDTO(
            novel_id=novel_id,
            chapter_number=chapter_number,
            gate_status=gate_status,
            chapter_status=chapter_status,
            review_status=review_status,
            can_enter_next=can_enter_next,
            can_lock=can_lock,
            word_count=word_count,
            issues=issues,
            suggestions=suggestions,
        )

    def lock_chapter(self, novel_id: str, chapter_number: int) -> ChapterQualityGateDTO:
        gate = self.evaluate(novel_id, chapter_number)
        if not gate.can_lock:
            return gate
        self.chapter_service.save_chapter_review(
            novel_id,
            chapter_number,
            LOCKED_REVIEW_STATUS,
            "作者已确认锁定；可作为后续强上下文候选。",
        )
        return self.evaluate(novel_id, chapter_number)

    def mark_synced(self, novel_id: str, chapter_number: int, memo: str = "") -> ChapterQualityGateDTO:
        self.chapter_service.save_chapter_review(
            novel_id,
            chapter_number,
            SYNCED_REVIEW_STATUS,
            memo or "章节已锁定并完成章后同步，可作为后续强上下文。",
        )
        return self.evaluate(novel_id, chapter_number)

    def mark_review_pending(self, novel_id: str, chapter_number: int, memo: str = "") -> ChapterQualityGateDTO:
        self.chapter_service.save_chapter_review(
            novel_id,
            chapter_number,
            REVIEW_PENDING_STATUS,
            memo or "正文已更新，等待作者审稿与锁定后再进入长期记忆。",
        )
        return self.evaluate(novel_id, chapter_number)

    def mark_revision_required(self, novel_id: str, chapter_number: int, memo: str = "") -> ChapterQualityGateDTO:
        self.chapter_service.save_chapter_review(
            novel_id,
            chapter_number,
            REVISION_REQUIRED_STATUS,
            memo or "章节质量门禁要求修订。",
        )
        return self.evaluate(novel_id, chapter_number)

    def list_issue_tasks(self, novel_id: str, chapter_number: int) -> list[ChapterIssueTaskDTO]:
        gate = self.evaluate(novel_id, chapter_number)
        tasks: list[ChapterIssueTaskDTO] = []
        for issue in gate.issues:
            tasks.append(ChapterIssueTaskDTO(
                id=f"gate:{chapter_number}:{issue.code}",
                source="quality_gate",
                code=issue.code,
                severity=issue.severity,
                title=issue.message,
                evidence=f"第 {chapter_number} 章正文，约 {gate.word_count} 字",
                basis="章节质量门禁：语义完整性、最低篇幅与作者审阅状态",
                confidence=0.92 if issue.severity == "blocker" else 0.78,
                recommended_action=issue.action,
            ))
        return tasks

    def preflight(
        self,
        novel_id: str,
        chapter_number: int,
        outline: str = "",
        context_preview: dict | None = None,
    ) -> ChapterPreflightDTO:
        gate = self.evaluate(novel_id, chapter_number)
        warnings: list[str] = []
        hard_conflicts: list[str] = []

        selected_outline = (outline or "").strip()
        outline_source = "frontend"
        blueprint = self._get_chapter_blueprint(novel_id, chapter_number)
        blueprint_outline = str(blueprint.get("outline") or "").strip()
        if self._outline_is_generic(selected_outline):
            chapter = self.chapter_service.get_chapter_by_novel_and_number(novel_id, chapter_number)
            selected_outline = blueprint_outline or getattr(chapter, "outline", "") or ""
            outline_source = "story_nodes.blueprint" if blueprint_outline else "chapters.outline" if selected_outline else "fallback"
            if not selected_outline:
                title = getattr(chapter, "title", "") or f"第{chapter_number}章"
                selected_outline = f"{title}。承接上一章状态，完成本章阶段性落点。"
                warnings.append("前端传入大纲过泛，已降级为章节标题与通用承接要求。")
        elif blueprint_outline and selected_outline != blueprint_outline:
            warnings.append("前端大纲与结构树蓝图不同；生成时应以结构树蓝图为权威。")

        if gate.review_status == REVISION_REQUIRED_STATUS:
            hard_conflicts.append("当前章节被标记为需修订，生成前应先确认是否重写或续写。")
        if gate.gate_status == "blocked":
            warnings.append("当前章节门禁处于阻断状态，本次生成应优先补全或重写问题段落。")

        if context_preview:
            token_usage = context_preview.get("token_usage") or {}
            total = int(token_usage.get("total") or 0)
            limit = int(token_usage.get("limit") or 0)
            if limit and total / limit > 0.9:
                warnings.append("上下文 token 使用率超过 90%，低优先级召回可能被压缩。")

        authority_lock = [
            f"当前章节：第 {chapter_number} 章",
            f"本章权威大纲来源：{outline_source}",
            f"本章权威大纲：{selected_outline[:500]}",
            f"章节门禁：{gate.gate_status} / 审阅状态：{gate.review_status}",
            "低优先级召回、旧摘要、自动抽取事实不得覆盖用户设定、Premise Lock 与本章权威大纲。",
        ]
        authority_lock.extend(self._blueprint_authority_lines(blueprint))

        return ChapterPreflightDTO(
            novel_id=novel_id,
            chapter_number=chapter_number,
            outline_source=outline_source,
            selected_outline=selected_outline,
            authority_lock=authority_lock,
            warnings=warnings,
            hard_conflicts=hard_conflicts,
            selected_authority=[
                "用户显式输入/作品设定锁定",
                "knowledge.premise_lock",
                "bible_style_notes",
                "story_nodes/chapters 当前章大纲",
                "Bible 角色表",
                "Triples / chapter summaries / 自动抽取状态",
            ],
        )

    def _get_chapter_blueprint(self, novel_id: str, chapter_number: int) -> dict:
        if not self.story_node_repository:
            return {}
        try:
            if hasattr(self.story_node_repository, "get_tree_sync"):
                tree = self.story_node_repository.get_tree_sync(novel_id)
                nodes = getattr(tree, "nodes", [])
            elif hasattr(self.story_node_repository, "get_by_novel_sync"):
                nodes = self.story_node_repository.get_by_novel_sync(novel_id)
            else:
                return {}
            node = next(
                (
                    n for n in nodes
                    if getattr(getattr(n, "node_type", None), "value", getattr(n, "node_type", None)) == "chapter"
                    and n.number == chapter_number
                ),
                None,
            )
            if not node:
                return {}
            blueprint = (node.metadata or {}).get("blueprint") or {}
            return blueprint if isinstance(blueprint, dict) else {}
        except Exception:
            return {}

    def _blueprint_authority_lines(self, blueprint: dict) -> list[str]:
        if not blueprint:
            return []
        lines: list[str] = []
        if blueprint.get("narrative_function"):
            lines.append(f"本章功能：{blueprint.get('narrative_function')}")
        if blueprint.get("target_tension"):
            lines.append(f"目标张力：{blueprint.get('target_tension')}/10（按计划执行，不要盲目追高）")
        if blueprint.get("tension_phase"):
            lines.append(f"张力阶段：{blueprint.get('tension_phase')}")
        for key, label in [
            ("must_happen", "必须发生"),
            ("must_not_happen", "不得发生/不得提前泄露"),
            ("handoff_to_next", "章末交接"),
        ]:
            value = blueprint.get(key)
            if isinstance(value, list) and value:
                lines.append(f"{label}：" + "；".join(str(v) for v in value))
            elif isinstance(value, str) and value.strip():
                lines.append(f"{label}：{value.strip()}")
        return lines

    def _detect_open_ending(self, content: str) -> Optional[ChapterGateIssueDTO]:
        text = (content or "").strip()
        if not text:
            return None
        if text[-1] in "，、：；—":
            return ChapterGateIssueDTO(
                code="open_ending",
                severity="blocker",
                message="结尾停在未完成标点，疑似截断。",
                action="使用续写补全或手动收束。",
            )
        if text.count("“") > text.count("”"):
            return ChapterGateIssueDTO(
                code="unclosed_dialogue",
                severity="blocker",
                message="结尾存在未闭合对话，疑似截断。",
                action="补全对话和场景落点。",
            )
        tail = text[-180:]
        dangling = ("就在这时", "下一刻", "突然", "他刚要", "她刚要", "正要", "还没来得及", "警报响起", "屏幕亮起")
        if any(token in tail for token in dangling) and not re.search(r"[。！？…]$", tail):
            return ChapterGateIssueDTO(
                code="dangling_action",
                severity="major",
                message="结尾像动作链或信息点悬而未落。",
                action="增加阶段性结果、情绪落点或明确章末钩子。",
            )
        return None

    def _outline_is_generic(self, outline: str) -> bool:
        text = (outline or "").strip()
        if len(text) < 24:
            return True
        generic_markers = ("承接前情", "推进主线", "保持人设", "叙事节奏一致")
        return sum(1 for marker in generic_markers if marker in text) >= 2
