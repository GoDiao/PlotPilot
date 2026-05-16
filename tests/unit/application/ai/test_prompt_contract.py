from application.ai.prompt_contract import (
    build_chapter_generation_contract,
    build_tension_revision_contract,
    infer_tension_policy,
)


def test_infer_tension_policy_allows_low_tension_buffer_chapters():
    policy = infer_tension_policy("目标张力：2/10；张力阶段：余波/缓冲")

    assert "可保持低到中等张力" in policy
    assert "不要为了刺激感强行制造冲突" in policy


def test_chapter_generation_contract_removes_mechanical_webnovel_rules():
    system, user = build_chapter_generation_contract(
        outline="低张力铺垫章，整理后果并交接线索。",
        length_rule="本段约 1000 字。",
        context="近期上下文",
    )
    combined = system + "\n" + user

    assert "Authority Lock" in combined
    assert "只在蓝图/场景需要时使用" in combined
    assert "必须有多个人物互动" not in combined
    assert "不少于3段对话" not in combined
    assert "结尾要有悬念或转折" not in combined


def test_revision_contract_is_patch_style_and_authority_safe():
    prompt = build_tension_revision_contract(
        diagnosis='{"suggestions":["补足章末承接"]}',
        target_text="目标张力：3/10；Authority Lock：主角李维",
        source_text="原文",
    )

    assert "只做局部 Diff 改稿" in prompt
    assert "不重写整章" in prompt
    assert "不改变主角" in prompt
    assert "主角李维" in prompt

