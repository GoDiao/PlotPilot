from __future__ import annotations

import difflib
import json
import uuid
from typing import Any

from application.core.services.chapter_service import ChapterService
from domain.ai.services.llm_service import GenerationConfig, LLMService
from domain.ai.value_objects.prompt import Prompt
from domain.shared.exceptions import EntityNotFoundError


class TrustworthyCreationService:
    def __init__(
        self,
        db,
        chapter_service: ChapterService,
        llm_service: LLMService | None = None,
        story_node_repository: Any = None,
    ) -> None:
        self.db = db
        self.chapter_service = chapter_service
        self.llm_service = llm_service
        self.story_node_repository = story_node_repository

    def add_memory_entry(
        self,
        novel_id: str,
        chapter_number: int,
        memory_layer: str,
        source: str,
        entry_type: str,
        content: str,
        payload: dict[str, Any] | None = None,
        issue_id: str | None = None,
    ) -> dict[str, Any]:
        entry_id = f"mem-{uuid.uuid4().hex}"
        self.db.execute(
            """
            INSERT INTO chapter_memory_entries
            (id, novel_id, chapter_number, memory_layer, source, entry_type, content, payload, issue_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                novel_id,
                chapter_number,
                memory_layer,
                source,
                entry_type,
                content,
                json.dumps(payload or {}, ensure_ascii=False),
                issue_id,
            ),
        )
        self.db.commit()
        return self.get_memory_entry(entry_id)

    def get_memory_entry(self, entry_id: str) -> dict[str, Any]:
        row = self.db.fetch_one("SELECT * FROM chapter_memory_entries WHERE id = ?", (entry_id,))
        if not row:
            raise ValueError(f"Memory entry not found: {entry_id}")
        return self._decode_json(row, "payload")

    def list_memory_entries(
        self,
        novel_id: str,
        chapter_number: int | None = None,
        memory_layer: str | None = None,
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM chapter_memory_entries WHERE novel_id = ?"
        params: list[Any] = [novel_id]
        if chapter_number is not None:
            sql += " AND chapter_number = ?"
            params.append(chapter_number)
        if memory_layer:
            sql += " AND memory_layer = ?"
            params.append(memory_layer)
        sql += " ORDER BY created_at DESC"
        return [self._decode_json(row, "payload") for row in self.db.fetch_all(sql, tuple(params))]

    def promote_memory_entry(self, entry_id: str, target_layer: str = "canonical") -> dict[str, Any]:
        self.db.execute(
            """
            UPDATE chapter_memory_entries
            SET memory_layer = ?, status = 'active', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (target_layer, entry_id),
        )
        self.db.commit()
        return self.get_memory_entry(entry_id)

    def apply_issue_action(
        self,
        novel_id: str,
        chapter_number: int,
        issue_id: str,
        action: str,
        memo: str = "",
    ) -> dict[str, Any]:
        action_id = f"act-{uuid.uuid4().hex}"
        self.db.execute(
            """
            INSERT INTO chapter_issue_actions
            (id, novel_id, chapter_number, issue_id, action, memo)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (action_id, novel_id, chapter_number, issue_id, action, memo),
        )
        if action == "accept_new_setting":
            self.add_memory_entry(
                novel_id,
                chapter_number,
                "pending",
                "issue_action",
                "accepted_setting",
                memo or issue_id,
                {"action_id": action_id, "issue_id": issue_id},
                issue_id=issue_id,
            )
        elif action == "mark_false_positive":
            self.add_memory_entry(
                novel_id,
                chapter_number,
                "draft",
                "issue_action",
                "false_positive",
                memo or issue_id,
                {"action_id": action_id, "issue_id": issue_id},
                issue_id=issue_id,
            )
        self.db.commit()
        return self.db.fetch_one("SELECT * FROM chapter_issue_actions WHERE id = ?", (action_id,))

    def create_snapshot(self, novel_id: str, chapter_number: int, reason: str = "") -> dict[str, Any]:
        chapter = self.chapter_service.get_chapter_by_novel_and_number(novel_id, chapter_number)
        if chapter is None:
            raise EntityNotFoundError("Chapter", f"{novel_id}/chapter-{chapter_number}")
        snapshot_id = f"snap-{uuid.uuid4().hex}"
        self.db.execute(
            """
            INSERT INTO chapter_snapshots (id, novel_id, chapter_number, content, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (snapshot_id, novel_id, chapter_number, chapter.content or "", reason),
        )
        self.db.commit()
        return self.db.fetch_one("SELECT * FROM chapter_snapshots WHERE id = ?", (snapshot_id,))

    def latest_snapshot(self, novel_id: str, chapter_number: int) -> dict[str, Any] | None:
        return self.db.fetch_one(
            """
            SELECT * FROM chapter_snapshots
            WHERE novel_id = ? AND chapter_number = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (novel_id, chapter_number),
        )

    def rollback_latest_snapshot(self, novel_id: str, chapter_number: int) -> dict[str, Any]:
        snapshot = self.latest_snapshot(novel_id, chapter_number)
        if not snapshot:
            raise ValueError("No chapter snapshot available")
        chapter = self.chapter_service.update_chapter_by_novel_and_number(
            novel_id,
            chapter_number,
            snapshot["content"],
        )
        return {"snapshot": snapshot, "chapter": chapter}

    async def create_tension_revision_drafts(
        self,
        novel_id: str,
        chapter_number: int,
        diagnosis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        chapter = self.chapter_service.get_chapter_by_novel_and_number(novel_id, chapter_number)
        if chapter is None:
            raise EntityNotFoundError("Chapter", f"{novel_id}/chapter-{chapter_number}")
        original = chapter.content or ""
        if not original.strip():
            raise ValueError("Chapter content is empty")

        blueprint = self._get_chapter_blueprint(novel_id, chapter_number)
        authority_lock = self._format_blueprint_authority_lock(blueprint)
        variants = self._revision_variants_for_blueprint(blueprint)
        drafts: list[dict[str, Any]] = []
        self.create_snapshot(novel_id, chapter_number, "tension_revision")
        for label, instruction in variants:
            revised = await self._revise_content(original, diagnosis, instruction, authority_lock)
            drafts.append(self._store_revision_draft(novel_id, chapter_number, label, original, revised))
        return drafts

    def list_revision_drafts(self, novel_id: str, chapter_number: int) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT * FROM chapter_revision_drafts
            WHERE novel_id = ? AND chapter_number = ?
            ORDER BY created_at DESC
            """,
            (novel_id, chapter_number),
        )

    def apply_revision_draft(self, draft_id: str) -> dict[str, Any]:
        draft = self.db.fetch_one("SELECT * FROM chapter_revision_drafts WHERE id = ?", (draft_id,))
        if not draft:
            raise ValueError(f"Revision draft not found: {draft_id}")
        self.create_snapshot(draft["novel_id"], int(draft["chapter_number"]), "before_apply_revision")
        chapter = self.chapter_service.update_chapter_by_novel_and_number(
            draft["novel_id"],
            int(draft["chapter_number"]),
            draft["revised_content"],
        )
        self.db.execute(
            """
            UPDATE chapter_revision_drafts
            SET status = 'applied', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (draft_id,),
        )
        self.db.commit()
        return {
            "draft": self.db.fetch_one("SELECT * FROM chapter_revision_drafts WHERE id = ?", (draft_id,)),
            "chapter": chapter,
        }

    async def _revise_content(
        self,
        original: str,
        diagnosis: dict[str, Any],
        instruction: str,
        authority_lock: str = "",
    ) -> str:
        if self.llm_service is None:
            return self._fallback_revision(original, diagnosis, instruction)
        system = "你是长篇小说修订总编。只输出修订后的完整正文，不要解释。"
        lock_block = f"本章 Authority Lock（不得违反）:\n{authority_lock}\n\n" if authority_lock.strip() else ""
        user = (
            f"{lock_block}"
            f"修订策略：{instruction}\n"
            f"张力诊断：{json.dumps(diagnosis, ensure_ascii=False)}\n\n"
            f"原文：\n{original}\n\n"
            "要求：保留人物姓名、POV、世界设定和主要事件；只修改需要修订的段落；"
            "按计划目标张力修订，不要默认把所有章节推成高张力；必须保留章末承接。"
        )
        result = await self.llm_service.generate(
            Prompt(system=system, user=user),
            GenerationConfig(max_tokens=max(2048, min(12000, len(original) * 2)), temperature=0.55),
        )
        return result.content.strip() or self._fallback_revision(original, diagnosis, instruction)

    def _fallback_revision(self, original: str, diagnosis: dict[str, Any], instruction: str) -> str:
        suggestions = diagnosis.get("suggestions") or []
        note = "\n\n【修订提示】" + instruction
        if suggestions:
            note += "\n" + "\n".join(f"- {item}" for item in suggestions[:3])
        return original.rstrip() + note

    def _revision_variants_for_blueprint(self, blueprint: dict[str, Any]) -> list[tuple[str, str]]:
        target = self._coerce_target_tension(blueprint)
        function = str(blueprint.get("narrative_function") or "").lower()
        is_low_target = target is not None and target <= 4
        is_cooldown = function in {"cooldown", "transition", "aftermath", "setup"}
        if is_low_target or is_cooldown:
            return [
                ("conservative", "保守贴合版：尽量保留原文，只补足计划必写事件、后果和章末承接。"),
                ("quiet_tension", "低张力精修版：维持余波/铺垫/过渡功能，通过不安、信息差和情绪余震增强可读性，不升级成大冲突。"),
                ("pace_clarity", "节奏澄清版：压缩松散过渡，强化场景目标、人物反应和下一章交接。"),
            ]
        return [
            ("conservative", "保守增强版：尽量保留原文，只补足张力、代价和章末落点。"),
            ("high_conflict", "强冲突版：提高外部阻力和人物选择代价，但不改变核心设定。"),
            ("pace_compress", "节奏压缩版：删减松散过渡，让冲突更快进入有效场景。"),
        ]

    def _get_chapter_blueprint(self, novel_id: str, chapter_number: int) -> dict[str, Any]:
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
                    item for item in nodes
                    if getattr(getattr(item, "node_type", None), "value", getattr(item, "node_type", None)) == "chapter"
                    and getattr(item, "number", None) == chapter_number
                ),
                None,
            )
            blueprint = ((getattr(node, "metadata", None) or {}).get("blueprint") if node else {}) or {}
            return blueprint if isinstance(blueprint, dict) else {}
        except Exception:
            return {}

    def _format_blueprint_authority_lock(self, blueprint: dict[str, Any]) -> str:
        if not blueprint:
            return ""
        lines: list[str] = []
        if blueprint.get("outline"):
            lines.append(f"本章大纲：{blueprint.get('outline')}")
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
                lines.append(f"{label}：" + "；".join(str(item) for item in value))
            elif isinstance(value, str) and value.strip():
                lines.append(f"{label}：{value.strip()}")
        return "\n".join(lines)

    @staticmethod
    def _coerce_target_tension(blueprint: dict[str, Any]) -> int | None:
        try:
            value = blueprint.get("target_tension")
            if value is None:
                return None
            return max(1, min(10, int(float(value))))
        except (TypeError, ValueError):
            return None

    def _store_revision_draft(
        self,
        novel_id: str,
        chapter_number: int,
        variant_label: str,
        original: str,
        revised: str,
    ) -> dict[str, Any]:
        draft_id = f"rev-{uuid.uuid4().hex}"
        diff_text = "\n".join(
            difflib.unified_diff(
                original.splitlines(),
                revised.splitlines(),
                fromfile="original",
                tofile=variant_label,
                lineterm="",
            )
        )
        self.db.execute(
            """
            INSERT INTO chapter_revision_drafts
            (id, novel_id, chapter_number, source, variant_label, original_content, revised_content, diff_text)
            VALUES (?, ?, ?, 'tension', ?, ?, ?, ?)
            """,
            (draft_id, novel_id, chapter_number, variant_label, original, revised, diff_text),
        )
        self.db.commit()
        return self.db.fetch_one("SELECT * FROM chapter_revision_drafts WHERE id = ?", (draft_id,))

    def _decode_json(self, row: dict[str, Any], key: str) -> dict[str, Any]:
        next_row = dict(row)
        try:
            next_row[key] = json.loads(next_row.get(key) or "{}")
        except Exception:
            next_row[key] = {}
        return next_row
