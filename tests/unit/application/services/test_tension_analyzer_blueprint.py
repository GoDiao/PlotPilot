from unittest.mock import AsyncMock, Mock

import pytest

from application.analyst.services.tension_analyzer import TensionAnalyzer
from application.workbench.dtos.writer_block_dto import TensionSlingshotRequest
from domain.structure.story_node import NodeType, StoryNode, StoryTree


@pytest.mark.asyncio
async def test_tension_analyzer_uses_chapter_blueprint_as_standard():
    event_repo = Mock()
    event_repo.list_up_to_chapter.return_value = []
    llm_client = Mock()
    llm_client.generate = AsyncMock(return_value="""{
        "diagnosis": "本章是铺垫章，低张力符合计划。",
        "tension_level": "low",
        "missing_elements": [],
        "suggestions": ["设置下一章承接钩子"]
    }""")
    story_repo = Mock()
    story_repo.get_tree_sync.return_value = StoryTree(
        novel_id="novel-1",
        nodes=[
            StoryNode(
                id="chapter-node-2",
                novel_id="novel-1",
                node_type=NodeType.CHAPTER,
                number=2,
                title="缓冲章",
                order_index=2,
                metadata={
                    "blueprint": {
                        "outline": "李维整理遗迹线索。",
                        "narrative_function": "cooldown",
                        "target_tension": 3,
                        "tension_phase": "余波",
                    }
                },
            )
        ],
    )
    analyzer = TensionAnalyzer(
        event_repo,
        llm_client,
        chapter_repository=None,
        plot_arc_repository=None,
        story_node_repository=story_repo,
    )

    result = await analyzer.analyze_tension(TensionSlingshotRequest(novel_id="novel-1", chapter_number=2))

    prompt = llm_client.generate.call_args[0][0]
    assert "目标张力: 3/10" in prompt
    assert "不是越高越好" in prompt
    assert result.target_tension == 3
    assert result.planned_function == "cooldown"
