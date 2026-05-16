"""Shared prompt contract blocks for trustworthy long-form creation.

These helpers keep generation, diagnosis, and revision prompts aligned around
the same control-console contract instead of duplicating genre-specific rules.
"""

from __future__ import annotations

from typing import Iterable


LOW_TENSION_HINTS = ("低", "缓", "铺垫", "余波", "过渡", "冷却", "setup", "cooldown")
HIGH_TENSION_HINTS = ("高", "高潮", "爆发", "危机", "决战", "climax", "crisis")


def _clean_lines(lines: Iterable[str]) -> list[str]:
    return [line.strip() for line in lines if line and line.strip()]


def infer_tension_policy(text: str = "") -> str:
    """Return blueprint-aware tension guidance from free-form planning text."""
    lowered = (text or "").lower()
    if any(hint in lowered for hint in LOW_TENSION_HINTS):
        return (
            "本章/本节拍可保持低到中等张力；重点写清铺垫、余波、关系变化或信息交接，"
            "不要为了刺激感强行制造冲突、打斗、反转或章末钩子。"
        )
    if any(hint in lowered for hint in HIGH_TENSION_HINTS):
        return (
            "本章/本节拍应兑现高张力目标；冲突、阻碍、代价和选择必须外化，"
            "但仍不得违反 Authority Lock。"
        )
    return (
        "按章节蓝图决定张力强度；不要默认把每章写成高潮，也不要默认每章都用悬念结尾。"
    )


def build_chapter_generation_contract(
    *,
    outline: str,
    length_rule: str,
    beat_extra: str = "",
    planning_section: str = "",
    voice_block: str = "",
    context: str = "",
    fact_lock: str = "",
) -> tuple[str, str]:
    """Build system/user messages for chapter generation.

    The contract is intentionally genre-neutral. Genre presets may add style,
    but they must not override the authority lock or blueprint target tension.
    """
    planning_text = f"{planning_section}\n{outline}"
    tension_policy = infer_tension_policy(planning_text)
    system_message = f"""你是长篇小说创作控制台的章节写作引擎。请根据上下文与章节蓝图撰写中文小说正文。

【Authority Lock / 上下文权威】
- 用户显式设定、Premise Lock、Bible 核心设定、章节蓝图和当前章大纲优先级最高。
- 低优先级召回、旧摘要、自动抽取状态只能作为参考；如有冲突，不得覆盖权威设定。
- 保持主角/POV/核心身份/关键地点/时间线连续，不要引入同名替身或身份漂移。

【Context Package】
{planning_section}{voice_block}{context}

{fact_lock}

【Writing Contract】
1. 写成完整小说正文场景，不写提纲、复盘、说明书或元评论。
2. 按章节蓝图完成本章功能、必写事件、禁写事项和章末承接点。
3. {tension_policy}
4. 对话、多人互动、冲突和悬念只在蓝图/场景需要时使用；不得机械凑数量。
5. 场景要具体，有动作、感官、心理与因果推进；避免空泛概述。
6. {length_rule}
7. 用中文写作，默认第三人称；如 Authority Lock 指定 POV，以 Authority Lock 为准。{beat_extra}"""

    user_message = f"""【Current Task / 当前任务】
根据以下章节大纲与蓝图写正文：

{outline}

【Output Contract / 输出契约】
- 只输出正文，不输出章节标题、分析、JSON 或解释。
- 不强行制造高张力；目标是符合计划张力与本章叙事功能。
- 不改写已生成正文，不复述已发生情节。
- 如果上下文冲突，以 Authority Lock 和本章蓝图为准。"""
    return system_message, user_message


def build_tension_revision_contract(*, diagnosis: str, target_text: str, source_text: str) -> str:
    """Build a conservative patch-style revision prompt."""
    policy = infer_tension_policy(target_text)
    return f"""你是长篇小说控制台的保守修订引擎，只做局部 Diff 改稿。

【Revision Contract】
- 只修改诊断命中的段落或节拍，不重写整章。
- 不改变主角、POV、世界观锁、章节蓝图、已发生事实和章末承接点。
- {policy}
- 保留原文可用内容，优先增强因果、动作、情绪递进和场景清晰度。

【诊断】
{diagnosis}

【修订目标】
{target_text}

【原文】
{source_text}

请输出改稿正文；不要输出解释。"""


def build_blueprint_planning_principles() -> str:
    """Shared planning principles for act/chapter blueprint prompts."""
    return """【蓝图规划原则】
- 张力曲线要有起伏：铺垫、推进、余波、缓冲、高潮都可以是有效章节功能。
- 不要让每幕、每章都默认高冲突或悬念结尾；按全书节奏安排目标张力。
- 每个章节蓝图必须能指导正文写作：功能、目标张力、必写事件、禁写事项、承接点要清楚。
- 章末承接点服务下一章连续性，不等同于强行 cliffhanger。"""


def build_memory_extraction_guard() -> str:
    """Shared guard for post-chapter memory and knowledge extraction prompts."""
    return """【Memory Commit Guard / 记忆提交防污染】
- 只抽取正文中明确出现、可被文本证据支持的事实；不要把推测、修辞、梦境或错误生成当成设定。
- 新人物、新地点、新关系、新伏笔默认是候选事实；若与主角/POV/核心身份高度重合但姓名不同，应标记为疑似漂移，不要升级为权威设定。
- 旧摘要、召回内容和自动抽取状态不得覆盖 Premise Lock、Bible 核心设定、Authority Lock 或章节蓝图。
- 伏笔回收必须与待回收清单高度匹配；不要因为主题相似就判定已回收。
- 时间线事件必须来自本章明确叙述；不确定时间点应写相对描述，不要编造历法。"""


def build_review_guard() -> str:
    """Shared guard for consistency review prompts."""
    return """【Review Guard / 审稿证据规则】
- 每条问题必须基于正文证据和设定依据；不能只因为角色未在局部资料中出现就直接判严重错误。
- 如果资料缺失或上下文不足，优先输出 warning/suggestion，并说明需要用户确认。
- 低优先级历史摘要与高优先级设定冲突时，应提示冲突来源，不得建议覆盖权威设定。
- 建议动作要可执行：修正文稿、更新 Bible、标记误报、接受新设定或暂不入库。"""
