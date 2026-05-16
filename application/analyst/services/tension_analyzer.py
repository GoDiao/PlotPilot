"""Tension analyzer service."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from application.ai.structured_json_pipeline import (
    parse_and_repair_json,
    sanitize_llm_output,
    validate_json_schema,
)
from application.ai.prompt_contract import infer_tension_policy
from application.analyst.tension.schema import TensionDiagnosisLlmPayload
from application.workbench.dtos.writer_block_dto import TensionDiagnosis, TensionSlingshotRequest
from domain.novel.repositories.chapter_repository import ChapterRepository
from domain.novel.repositories.narrative_event_repository import NarrativeEventRepository
from domain.novel.repositories.plot_arc_repository import PlotArcRepository
from domain.novel.value_objects.novel_id import NovelId

_CHAPTER_EXCERPT_MAX_CHARS = 3500


def _excerpt_chapter_text(text: str, max_chars: int = _CHAPTER_EXCERPT_MAX_CHARS) -> str:
    stripped = (text or "").strip()
    if len(stripped) <= max_chars:
        return stripped
    half = max_chars // 2
    return stripped[:half] + "\n……\n" + stripped[-half:]


class TensionAnalyzer:
    """Analyze chapter tension against the planned writing blueprint."""

    def __init__(
        self,
        event_repository: NarrativeEventRepository,
        llm_client,
        chapter_repository: Optional[ChapterRepository] = None,
        plot_arc_repository: Optional[PlotArcRepository] = None,
        story_node_repository: Any = None,
    ) -> None:
        self._event_repository = event_repository
        self._llm_client = llm_client
        self._chapter_repository = chapter_repository
        self._plot_arc_repository = plot_arc_repository
        self._story_node_repository = story_node_repository

    async def analyze_tension(self, request: TensionSlingshotRequest) -> TensionDiagnosis:
        events = self._event_repository.list_up_to_chapter(
            request.novel_id,
            request.chapter_number,
        )
        stats = self._analyze_statistics(events, request.chapter_number)
        blueprint = self._get_chapter_blueprint(request.novel_id, request.chapter_number)
        extra_context = self._build_repository_context(request, blueprint)
        prompt = self._build_prompt(events, stats, request, extra_context)
        response = await self._llm_client.generate(prompt)
        return self._parse_response(response, blueprint)

    def _build_repository_context(
        self,
        request: TensionSlingshotRequest,
        blueprint: Optional[Dict[str, Any]] = None,
    ) -> str:
        blocks: List[str] = []
        novel_id_vo = NovelId(value=request.novel_id)

        if blueprint:
            blocks.append(self._format_blueprint_context(blueprint))

        if self._chapter_repository is not None:
            chapters = self._chapter_repository.list_by_novel(novel_id_vo)
            current = next(
                (chapter for chapter in chapters if chapter.number == request.chapter_number),
                None,
            )
            if current is not None:
                excerpt = _excerpt_chapter_text(current.content)
                if excerpt:
                    blocks.append(f"当前章正文摘录（可能截断）:\n{excerpt}")
                blocks.append(
                    "库内章节张力字段（0-100，仅作参考）: "
                    f"tension_score={current.tension_score:.0f}, "
                    f"plot_tension={current.plot_tension:.0f}, "
                    f"emotional_tension={current.emotional_tension:.0f}, "
                    f"pacing_tension={current.pacing_tension:.0f}"
                )
            else:
                blocks.append(
                    f"库中未找到第 {request.chapter_number} 章实体，暂无正文/张力字段。"
                )

        if self._plot_arc_repository is not None:
            arc = self._plot_arc_repository.get_by_novel_id(novel_id_vo)
            if arc is not None:
                expected = arc.get_expected_tension(request.chapter_number)
                line = (
                    f"情节弧（slug={arc.slug}）按锚点插值的期望张力档位: "
                    f"{expected.name}（数值 {expected.value}，1=LOW ~ 4=PEAK）"
                )
                next_point = arc.get_next_plot_point(request.chapter_number)
                if next_point is not None:
                    desc = (next_point.description or "").strip()
                    if len(desc) > 220:
                        desc = desc[:220] + "……"
                    line += f"；下一剧情点: 第{next_point.chapter_number}章 - {desc}"
                blocks.append(line)
            else:
                blocks.append("库中暂无该小说的剧情弧记录。")

        return "\n\n".join(blocks) if blocks else ""

    def _format_blueprint_context(self, blueprint: Dict[str, Any]) -> str:
        lines: List[str] = ["本章结构蓝图（最高优先级评判标准）:"]
        if blueprint.get("narrative_function"):
            lines.append(f"- 计划功能: {blueprint.get('narrative_function')}")
        if blueprint.get("target_tension"):
            lines.append(f"- 目标张力: {blueprint.get('target_tension')}/10")
        if blueprint.get("tension_phase"):
            lines.append(f"- 张力阶段: {blueprint.get('tension_phase')}")
        if blueprint.get("outline"):
            lines.append(f"- 本章大纲: {blueprint.get('outline')}")
        for key, label in [
            ("must_happen", "必须发生"),
            ("must_not_happen", "不得发生/不得提前泄露"),
            ("handoff_to_next", "章末承接"),
        ]:
            value = blueprint.get(key)
            if isinstance(value, list) and value:
                lines.append(f"- {label}: " + "；".join(str(item) for item in value))
            elif isinstance(value, str) and value.strip():
                lines.append(f"- {label}: {value.strip()}")
        lines.append("- 判断原则: 张力不是越高越好，实际张力应服务计划功能与目标张力。")
        return "\n".join(lines)

    def _get_chapter_blueprint(self, novel_id: str, chapter_number: int) -> Dict[str, Any]:
        if self._story_node_repository is None:
            return {}
        try:
            if hasattr(self._story_node_repository, "get_tree_sync"):
                tree = self._story_node_repository.get_tree_sync(novel_id)
                nodes = getattr(tree, "nodes", [])
            elif hasattr(self._story_node_repository, "get_by_novel_sync"):
                nodes = self._story_node_repository.get_by_novel_sync(novel_id)
            else:
                return {}
            chapter_node = next(
                (
                    node
                    for node in nodes
                    if getattr(getattr(node, "node_type", None), "value", getattr(node, "node_type", None)) == "chapter"
                    and getattr(node, "number", None) == chapter_number
                ),
                None,
            )
            if chapter_node is None:
                return {}
            metadata = getattr(chapter_node, "metadata", None) or {}
            blueprint = metadata.get("blueprint") or {}
            return blueprint if isinstance(blueprint, dict) else {}
        except Exception:
            return {}

    def _analyze_statistics(self, events: List[dict], target_chapter: int) -> Dict:
        target_events = [event for event in events if event["chapter_number"] == target_chapter]
        prev_events = [event for event in events if event["chapter_number"] == target_chapter - 1]
        next_events = [event for event in events if event["chapter_number"] == target_chapter + 1]

        conflict_tags: List[str] = []
        emotion_tags: List[str] = []
        for event in target_events:
            tags = event.get("tags", [])
            conflict_tags.extend(tag for tag in tags if isinstance(tag, str) and tag.startswith("冲突:"))
            emotion_tags.extend(tag for tag in tags if isinstance(tag, str) and tag.startswith("情绪:"))

        chapters_with_data = {event["chapter_number"] for event in events}
        chapter_count = len(chapters_with_data)
        event_density = len(events) / chapter_count if chapter_count > 0 else 0.0

        return {
            "target_event_count": len(target_events),
            "prev_event_count": len(prev_events),
            "next_event_count": len(next_events),
            "conflict_count": len(conflict_tags),
            "emotion_diversity": len(set(emotion_tags)),
            "event_density": event_density,
            "chapters_with_narrative_count": chapter_count,
            "conflict_tags": conflict_tags,
            "emotion_tags": emotion_tags,
        }

    def _build_prompt(
        self,
        events: List[dict],
        stats: Dict,
        request: TensionSlingshotRequest,
        repository_context: str,
    ) -> str:
        event_summaries: List[str] = []
        for event in events:
            tags = event.get("tags", []) or []
            tags_str = ", ".join(str(tag) for tag in tags)
            event_summaries.append(
                f"第{event['chapter_number']}章: {event['event_summary']} (标签: {tags_str})"
            )

        events_text = "\n".join(event_summaries) if event_summaries else "暂无事件数据"
        repo_block = f"\n补充上下文（仓储）:\n{repository_context.strip()}\n" if repository_context.strip() else ""
        stuck_reason_text = f"\n作者自述的卡文原因: {request.stuck_reason}\n" if request.stuck_reason else ""
        density_note = "事件密度 = 已加载叙事事件总数 / 其中出现过的不同章节数；分母不是全书总章节数。"

        stats_text = f"""
统计数据:
- 目标章节事件数: {stats['target_event_count']}
- 上一章事件数: {stats['prev_event_count']}
- 下一章事件数: {stats['next_event_count']}
- 冲突标签数: {stats['conflict_count']}
- 情绪多样性（目标章不重复情绪标签数）: {stats['emotion_diversity']}
- 有叙事数据的章节数: {stats['chapters_with_narrative_count']}
- 事件密度: {stats['event_density']:.2f}（{density_note}）
- 冲突类型: {', '.join(stats['conflict_tags']) if stats['conflict_tags'] else '无'}
- 情绪类型: {', '.join(stats['emotion_tags']) if stats['emotion_tags'] else '无'}
"""

        tension_policy = infer_tension_policy(repository_context)

        return f"""你是小说创作控制台的张力审稿员，专门判断章节是否符合计划张力，而不是盲目追高。

当前小说ID: {request.novel_id}
卡文章节: 第{request.chapter_number}章
{stuck_reason_text}
事件列表:
{events_text}
{repo_block}
{stats_text}

请分析当前章节是否贴合蓝图目标、上下文承接和下一章需要，诊断卡文原因，并提供具体可操作的建议。

计划张力原则: {tension_policy}

要求:
1. 诊断要结合统计数据、事件内容与补充上下文（若有）。
2. 张力水平分为: low（低）、medium（中）、high（高）。
3. 缺失元素可包括: conflict、stakes、action、consequence、rising_tension、external_conflict、internal_conflict 等。
4. 建议必须是动作导向的，优先使用“补足”“压缩”“承接”“兑现”“延后”“澄清”等控制台式动作；只有目标张力不足时才使用“增加/强化”。
5. 建议要具体，不要泛泛而谈。
6. 如果补充上下文存在“本章结构蓝图”，请以计划功能、目标张力、张力阶段为标准：铺垫/余波/过渡章低张力可以通过；爆点/反转/揭示章低于计划才判为需要加强。
7. 不要把所有章节都建议改成高张力；建议应指向“贴合计划张力”和“下一章承接”。

请以 JSON 格式返回结果:
{{
    "diagnosis": "诊断结果，2-3句话",
    "tension_level": "low/medium/high",
    "missing_elements": ["缺失元素1", "缺失元素2"],
    "suggestions": ["具体建议1", "具体建议2", "具体建议3"]
}}
"""

    def _parse_response(self, response: str, blueprint: Optional[Dict[str, Any]] = None) -> TensionDiagnosis:
        blueprint = blueprint or {}
        cleaned = sanitize_llm_output(response)
        data, parse_errors = parse_and_repair_json(cleaned)
        if data is None:
            return self._diagnosis_with_blueprint(
                diagnosis="无法解析 LLM 返回的 JSON: " + "; ".join(parse_errors[:4]),
                tension_level="low",
                missing_elements=["parse_error"],
                suggestions=["请稍后重试，或检查模型输出是否被截断"],
                blueprint=blueprint,
            )

        payload, schema_errors = validate_json_schema(data, TensionDiagnosisLlmPayload)
        if payload is None:
            return self._diagnosis_with_blueprint(
                diagnosis="JSON 结构校验失败: " + "; ".join(schema_errors[:6]),
                tension_level="low",
                missing_elements=["schema_error"],
                suggestions=["请稍后重试"],
                blueprint=blueprint,
            )

        return self._diagnosis_with_blueprint(
            diagnosis=payload.diagnosis,
            tension_level=payload.tension_level,
            missing_elements=list(payload.missing_elements),
            suggestions=list(payload.suggestions),
            blueprint=blueprint,
        )

    def _diagnosis_with_blueprint(
        self,
        diagnosis: str,
        tension_level: str,
        missing_elements: List[str],
        suggestions: List[str],
        blueprint: Dict[str, Any],
    ) -> TensionDiagnosis:
        return TensionDiagnosis(
            diagnosis=diagnosis,
            tension_level=tension_level,
            missing_elements=missing_elements,
            suggestions=suggestions,
            target_tension=self._coerce_target_tension(blueprint),
            target_tension_source="story_nodes.metadata.blueprint" if blueprint else None,
            planned_function=blueprint.get("narrative_function") if blueprint else None,
            tension_phase=blueprint.get("tension_phase") if blueprint else None,
        )

    @staticmethod
    def _coerce_target_tension(blueprint: Dict[str, Any]) -> Optional[int]:
        try:
            value = blueprint.get("target_tension")
            if value is None:
                return None
            return max(1, min(10, int(float(value))))
        except (TypeError, ValueError):
            return None
