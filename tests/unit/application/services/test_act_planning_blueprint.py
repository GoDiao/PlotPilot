import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from application.blueprint.services.continuous_planning_service import ContinuousPlanningService
from domain.novel.entities.chapter import Chapter
from domain.structure.story_node import NodeType, PlanningSource, PlanningStatus, StoryNode


class FakeStoryNodeRepo:
    def __init__(self, act):
        self.act = act
        self.saved_batch = []
        self.updated = None

    async def get_by_id(self, node_id):
        return self.act if node_id == self.act.id else None

    def get_children_sync(self, parent_id):
        return self.saved_batch if parent_id == self.act.id else []

    async def delete(self, node_id):
        return True

    async def save_batch(self, nodes):
        self.saved_batch = nodes
        return nodes

    async def update(self, node):
        self.updated = node
        return node


class FakeChapterRepo:
    def __init__(self):
        self.saved = []

    def list_by_novel(self, novel_id):
        return []

    def save(self, chapter: Chapter):
        self.saved.append(chapter)
        return chapter

    def delete(self, chapter_id):
        return True


@pytest.mark.asyncio
async def test_confirm_act_planning_stores_blueprint_and_syncs_outlines():
    act = StoryNode(
        id="act-1",
        novel_id="novel-1",
        node_type=NodeType.ACT,
        number=1,
        title="第一幕",
        order_index=10,
        planning_status=PlanningStatus.CONFIRMED,
        planning_source=PlanningSource.AI_MACRO,
    )
    story_repo = FakeStoryNodeRepo(act)
    chapter_repo = FakeChapterRepo()
    element_repo = Mock()
    element_repo.delete_by_chapter = AsyncMock()
    element_repo.save_batch = AsyncMock()
    service = ContinuousPlanningService(
        story_node_repo=story_repo,
        chapter_element_repo=element_repo,
        llm_service=Mock(),
        chapter_repository=chapter_repo,
    )

    result = await service.confirm_act_planning(
        "act-1",
        [
            {
                "title": "遗迹入口",
                "outline": "李维抵达遗迹入口，并决定进入。",
                "blueprint": {
                    "narrative_function": "setup",
                    "target_tension": 3,
                    "tension_phase": "铺垫",
                    "outline": "李维抵达遗迹入口，并决定进入。",
                    "must_happen": ["确认入口坐标"],
                    "handoff_to_next": "下一章从开门接起",
                },
            }
        ],
    )

    assert result["created_chapters"] == 1
    story_node = story_repo.saved_batch[0]
    chapter = chapter_repo.saved[0]
    assert story_node.outline == "李维抵达遗迹入口，并决定进入。"
    assert chapter.outline == "李维抵达遗迹入口，并决定进入。"
    assert story_node.metadata["blueprint"]["target_tension"] == 3
    assert story_node.metadata["blueprint"]["narrative_function"] == "setup"
