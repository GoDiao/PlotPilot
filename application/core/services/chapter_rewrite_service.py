from __future__ import annotations

import json
import uuid
from typing import Any

from domain.shared.exceptions import EntityNotFoundError


class ChapterRewriteService:
    """Create pre-write snapshots and reset a chapter for true rewrite."""

    SNAPSHOT_TABLES = [
        "chapters",
        "chapter_reviews",
        "chapter_memory_entries",
        "chapter_issue_actions",
        "chapter_revision_drafts",
        "chapter_snapshots",
        "chapter_summaries",
        "narrative_events",
        "chapter_style_scores",
        "reader_simulations",
        "plot_points",
        "novel_foreshadow_registry",
        "timeline_registries",
        "memory_engine_state",
        "bibles",
        "bible_characters",
        "bible_character_relationships",
        "bible_world_settings",
        "bible_locations",
        "bible_timeline_notes",
        "bible_style_notes",
        "storylines",
        "storyline_milestones",
        "voice_fingerprint",
        "triples",
        "triple_attr",
        "triple_tags",
        "triple_more_chapters",
        "triple_provenance",
    ]

    CHAPTER_SCOPED_TABLES = [
        "chapter_reviews",
        "chapter_memory_entries",
        "chapter_issue_actions",
        "chapter_revision_drafts",
        "chapter_snapshots",
        "chapter_summaries",
        "narrative_events",
        "chapter_style_scores",
        "reader_simulations",
        "plot_points",
    ]

    def __init__(self, db, story_node_repo=None):
        self.db = db
        self.story_node_repo = story_node_repo
        self.ensure_tables()

    def ensure_tables(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS chapter_rewrite_snapshots (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL,
                chapter_number INTEGER NOT NULL,
                scope TEXT NOT NULL DEFAULT 'pre_write',
                reason TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                payload TEXT NOT NULL DEFAULT '{}',
                warnings TEXT NOT NULL DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                restored_at TIMESTAMP
            )
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chapter_rewrite_snapshots_scope
            ON chapter_rewrite_snapshots(novel_id, chapter_number, status, created_at)
            """
        )
        self.db.commit()

    def create_prewrite_snapshot(self, novel_id: str, chapter_number: int, reason: str = "pre_write") -> dict[str, Any]:
        self.ensure_tables()
        payload = self._collect_snapshot_payload(novel_id, chapter_number)
        snapshot_id = f"rewrite-snap-{uuid.uuid4().hex}"
        self.db.execute(
            """
            INSERT INTO chapter_rewrite_snapshots
            (id, novel_id, chapter_number, scope, reason, status, payload, warnings)
            VALUES (?, ?, ?, 'pre_write', ?, 'active', ?, '[]')
            """,
            (snapshot_id, novel_id, int(chapter_number), reason, json.dumps(payload, ensure_ascii=False)),
        )
        self.db.commit()
        return self._get_snapshot(snapshot_id)

    def preview_reset(self, novel_id: str, chapter_number: int) -> dict[str, Any]:
        snapshot = self._latest_active_snapshot(novel_id, chapter_number)
        return {
            "has_snapshot": bool(snapshot),
            "mode": "snapshot_restore" if snapshot else "soft_reset",
            "snapshot": self._snapshot_summary(snapshot) if snapshot else None,
            "warnings": self._reset_warnings(novel_id, chapter_number, bool(snapshot)),
        }

    def reset_for_rewrite(self, novel_id: str, chapter_number: int, restore_content: bool = False) -> dict[str, Any]:
        self.ensure_tables()
        snapshot = self._latest_active_snapshot(novel_id, chapter_number)
        if snapshot:
            return self._restore_snapshot(snapshot, restore_content=restore_content)
        return self._soft_reset(novel_id, chapter_number)

    def _collect_snapshot_payload(self, novel_id: str, chapter_number: int) -> dict[str, Any]:
        conn = self.db.get_connection()
        chapter = self._fetch_one_table(conn, "chapters", "novel_id = ? AND number = ?", (novel_id, int(chapter_number)))
        story_node_id = self._story_node_id_for_chapter(novel_id, chapter_number)
        knowledge_ids = [row["id"] for row in self._fetch_table(conn, "knowledge", "novel_id = ?", (novel_id,))]
        triple_ids = self._chapter_related_triple_ids(conn, novel_id, chapter_number, story_node_id)
        storyline_ids = [row["id"] for row in self._fetch_table(conn, "storylines", "novel_id = ?", (novel_id,))]
        bible_character_ids = [row["id"] for row in self._fetch_table(conn, "bible_characters", "novel_id = ?", (novel_id,))]

        tables: dict[str, list[dict[str, Any]]] = {}
        table_queries: dict[str, tuple[str, tuple[Any, ...]]] = {
            "chapters": ("novel_id = ? AND number = ?", (novel_id, int(chapter_number))),
            "chapter_reviews": ("novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number))),
            "chapter_memory_entries": ("novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number))),
            "chapter_issue_actions": ("novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number))),
            "chapter_revision_drafts": ("novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number))),
            "chapter_snapshots": ("novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number))),
            "narrative_events": ("novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number))),
            "chapter_style_scores": ("novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number))),
            "reader_simulations": ("novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number))),
            "plot_points": ("chapter_number = ? AND plot_arc_id IN (SELECT id FROM plot_arcs WHERE novel_id = ?)", (int(chapter_number), novel_id)),
            "novel_foreshadow_registry": ("novel_id = ?", (novel_id,)),
            "timeline_registries": ("novel_id = ?", (novel_id,)),
            "memory_engine_state": ("novel_id = ?", (novel_id,)),
            "bibles": ("novel_id = ?", (novel_id,)),
            "bible_characters": ("novel_id = ?", (novel_id,)),
            "bible_world_settings": ("novel_id = ?", (novel_id,)),
            "bible_locations": ("novel_id = ?", (novel_id,)),
            "bible_timeline_notes": ("novel_id = ?", (novel_id,)),
            "bible_style_notes": ("novel_id = ?", (novel_id,)),
            "storylines": ("novel_id = ?", (novel_id,)),
            "voice_fingerprint": ("novel_id = ?", (novel_id,)),
            "triples": (self._in_clause("id", triple_ids, "novel_id = ? AND chapter_number = ?"), tuple(triple_ids) if triple_ids else (novel_id, int(chapter_number))),
            "triple_more_chapters": (self._in_clause("triple_id", triple_ids, "novel_id = ? AND chapter_number = ?"), tuple(triple_ids) if triple_ids else (novel_id, int(chapter_number))),
            "triple_provenance": (self._in_clause("triple_id", triple_ids, "novel_id = ?"), tuple(triple_ids) if triple_ids else (novel_id,)),
        }
        if story_node_id:
            table_queries["chapter_elements"] = ("chapter_id = ?", (story_node_id,))
            table_queries["chapter_scenes"] = ("chapter_id = ?", (story_node_id,))
        if knowledge_ids:
            table_queries["chapter_summaries"] = (
                self._in_clause("knowledge_id", knowledge_ids, "1 = 0") + " AND chapter_number = ?",
                tuple(knowledge_ids) + (int(chapter_number),),
            )
        if bible_character_ids:
            table_queries["bible_character_relationships"] = (
                self._in_clause("character_id", bible_character_ids, "1 = 0"),
                tuple(bible_character_ids),
            )
        if storyline_ids:
            table_queries["storyline_milestones"] = (
                self._in_clause("storyline_id", storyline_ids, "1 = 0"),
                tuple(storyline_ids),
            )
        if triple_ids:
            table_queries["triple_attr"] = (self._in_clause("triple_id", triple_ids, "1 = 0"), tuple(triple_ids))
            table_queries["triple_tags"] = (self._in_clause("triple_id", triple_ids, "1 = 0"), tuple(triple_ids))

        for table in self.SNAPSHOT_TABLES + ["chapter_elements", "chapter_scenes"]:
            if table not in table_queries or not self._table_exists(conn, table):
                continue
            where, params = table_queries[table]
            tables[table] = self._fetch_table(conn, table, where, params)

        return {
            "chapter": chapter,
            "story_node_id": story_node_id,
            "triple_ids": triple_ids,
            "tables": tables,
        }

    def _restore_snapshot(self, snapshot: dict[str, Any], restore_content: bool) -> dict[str, Any]:
        payload = json.loads(snapshot["payload"] or "{}")
        novel_id = snapshot["novel_id"]
        chapter_number = int(snapshot["chapter_number"])
        tables = payload.get("tables") or {}
        warnings = self._reset_warnings(novel_id, chapter_number, True)
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN")
            self._delete_snapshot_scope(conn, novel_id, chapter_number, payload)
            for table in self._restore_table_order(tables):
                rows = tables.get(table) or []
                if not self._table_exists(conn, table):
                    continue
                self._insert_rows(conn, table, rows)
            if not restore_content:
                self._clear_chapter_for_rewrite(conn, novel_id, chapter_number)
            conn.execute(
                "UPDATE chapter_rewrite_snapshots SET status = 'restored', restored_at = CURRENT_TIMESTAMP WHERE id = ?",
                (snapshot["id"],),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return {
            "mode": "snapshot_restore",
            "snapshot_id": snapshot["id"],
            "chapter_number": chapter_number,
            "restored_tables": sorted(tables.keys()),
            "warnings": warnings,
        }

    def _soft_reset(self, novel_id: str, chapter_number: int) -> dict[str, Any]:
        payload = self._collect_snapshot_payload(novel_id, chapter_number)
        warnings = self._reset_warnings(novel_id, chapter_number, False)
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN")
            self._delete_chapter_scoped(conn, novel_id, chapter_number, payload)
            self._clear_chapter_for_rewrite(conn, novel_id, chapter_number)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return {
            "mode": "soft_reset",
            "chapter_number": int(chapter_number),
            "cleared_tables": self.CHAPTER_SCOPED_TABLES + ["chapter_elements", "chapter_scenes"],
            "warnings": warnings,
        }

    def _delete_snapshot_scope(self, conn, novel_id: str, chapter_number: int, payload: dict[str, Any]) -> None:
        self._delete_chapter_scoped(conn, novel_id, chapter_number, payload)
        if self._table_exists(conn, "bible_character_relationships"):
            conn.execute(
                "DELETE FROM bible_character_relationships WHERE character_id IN (SELECT id FROM bible_characters WHERE novel_id = ?)",
                (novel_id,),
            )
        if self._table_exists(conn, "storyline_milestones"):
            conn.execute(
                "DELETE FROM storyline_milestones WHERE storyline_id IN (SELECT id FROM storylines WHERE novel_id = ?)",
                (novel_id,),
            )
        story_node_id = payload.get("story_node_id") or self._story_node_id_for_chapter(novel_id, chapter_number)
        triple_ids = sorted(set(payload.get("triple_ids") or []) | set(self._chapter_related_triple_ids(conn, novel_id, chapter_number, story_node_id)))
        if triple_ids:
            self._delete_by_ids(conn, "triple_attr", "triple_id", triple_ids)
            self._delete_by_ids(conn, "triple_tags", "triple_id", triple_ids)
            self._delete_by_ids(conn, "triple_more_chapters", "triple_id", triple_ids)
            self._delete_by_ids(conn, "triple_provenance", "triple_id", triple_ids)
            self._delete_by_ids(conn, "triples", "id", triple_ids)
        for table in [
            "novel_foreshadow_registry",
            "timeline_registries",
            "memory_engine_state",
            "bibles",
            "bible_characters",
            "bible_world_settings",
            "bible_locations",
            "bible_timeline_notes",
            "bible_style_notes",
            "storylines",
            "voice_fingerprint",
        ]:
            if self._table_exists(conn, table):
                conn.execute(f"DELETE FROM {table} WHERE novel_id = ?", (novel_id,))

    def _restore_table_order(self, tables: dict[str, list[dict[str, Any]]]) -> list[str]:
        preferred = [
            "chapters",
            "chapter_reviews",
            "chapter_memory_entries",
            "chapter_issue_actions",
            "chapter_revision_drafts",
            "chapter_snapshots",
            "chapter_summaries",
            "narrative_events",
            "chapter_style_scores",
            "reader_simulations",
            "plot_points",
            "chapter_elements",
            "chapter_scenes",
            "novel_foreshadow_registry",
            "timeline_registries",
            "memory_engine_state",
            "bibles",
            "bible_characters",
            "bible_character_relationships",
            "bible_world_settings",
            "bible_locations",
            "bible_timeline_notes",
            "bible_style_notes",
            "storylines",
            "storyline_milestones",
            "voice_fingerprint",
            "triples",
            "triple_attr",
            "triple_tags",
            "triple_more_chapters",
            "triple_provenance",
        ]
        ordered = [table for table in preferred if table in tables]
        ordered.extend(table for table in tables.keys() if table not in set(ordered))
        return ordered

    def _delete_chapter_scoped(self, conn, novel_id: str, chapter_number: int, payload: dict[str, Any]) -> None:
        for table in self.CHAPTER_SCOPED_TABLES:
            if not self._table_exists(conn, table):
                continue
            if table == "plot_points":
                conn.execute(
                    "DELETE FROM plot_points WHERE chapter_number = ? AND plot_arc_id IN (SELECT id FROM plot_arcs WHERE novel_id = ?)",
                    (int(chapter_number), novel_id),
                )
            elif table == "chapter_summaries":
                conn.execute(
                    "DELETE FROM chapter_summaries WHERE chapter_number = ? AND knowledge_id IN (SELECT id FROM knowledge WHERE novel_id = ?)",
                    (int(chapter_number), novel_id),
                )
            else:
                conn.execute(
                    f"DELETE FROM {table} WHERE novel_id = ? AND chapter_number = ?",
                    (novel_id, int(chapter_number)),
                )
        story_node_id = payload.get("story_node_id") or self._story_node_id_for_chapter(novel_id, chapter_number)
        if story_node_id:
            if self._table_exists(conn, "chapter_elements"):
                conn.execute("DELETE FROM chapter_elements WHERE chapter_id = ?", (story_node_id,))
            if self._table_exists(conn, "chapter_scenes"):
                conn.execute("DELETE FROM chapter_scenes WHERE chapter_id = ?", (story_node_id,))

    def _clear_chapter_for_rewrite(self, conn, novel_id: str, chapter_number: int) -> None:
        existing = conn.execute(
            "SELECT id FROM chapters WHERE novel_id = ? AND number = ?",
            (novel_id, int(chapter_number)),
        ).fetchone()
        if not existing:
            raise EntityNotFoundError("Chapter", f"{novel_id}/chapter-{chapter_number}")
        columns = self._table_columns(conn, "chapters")
        assignments = ["content = ''", "status = 'draft'", "updated_at = CURRENT_TIMESTAMP"]
        for column in ["tension_score", "plot_tension", "emotional_tension", "pacing_tension"]:
            if column in columns:
                assignments.append(f"{column} = 50.0")
        conn.execute(
            f"UPDATE chapters SET {', '.join(assignments)} WHERE novel_id = ? AND number = ?",
            (novel_id, int(chapter_number)),
        )

    def _reset_warnings(self, novel_id: str, chapter_number: int, has_snapshot: bool) -> list[str]:
        warnings: list[str] = []
        if not has_snapshot:
            warnings.append("未找到写前快照：仅清理本章可定位副作用，Bible/伏笔/全局记忆可能残留。")
        later = self.db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM chapters WHERE novel_id = ? AND number > ? AND status = 'completed'",
            (novel_id, int(chapter_number)),
        )
        if later and int(later.get("cnt") or 0) > 0:
            warnings.append(f"检测到 {later['cnt']} 个后续已完成章节；本次默认只回退本章。")
        return warnings

    def _latest_active_snapshot(self, novel_id: str, chapter_number: int) -> dict[str, Any] | None:
        row = self.db.fetch_one(
            """
            SELECT * FROM chapter_rewrite_snapshots
            WHERE novel_id = ? AND chapter_number = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
            """,
            (novel_id, int(chapter_number)),
        )
        return dict(row) if row else None

    def _get_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        row = self.db.fetch_one("SELECT * FROM chapter_rewrite_snapshots WHERE id = ?", (snapshot_id,))
        return dict(row) if row else {}

    def _snapshot_summary(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        payload = json.loads(snapshot.get("payload") or "{}")
        tables = payload.get("tables") or {}
        return {
            "id": snapshot.get("id"),
            "created_at": snapshot.get("created_at"),
            "reason": snapshot.get("reason"),
            "tables": {name: len(rows or []) for name, rows in tables.items()},
        }

    def _story_node_id_for_chapter(self, novel_id: str, chapter_number: int) -> str | None:
        if not self.story_node_repo:
            return None
        try:
            nodes = self.story_node_repo.get_by_novel_sync(novel_id)
            for node in nodes:
                if getattr(getattr(node, "node_type", None), "value", None) == "chapter" and int(node.number) == int(chapter_number):
                    return node.id
        except Exception:
            return None
        return None

    def _chapter_related_triple_ids(self, conn, novel_id: str, chapter_number: int, story_node_id: str | None) -> list[str]:
        ids = {row["id"] for row in self._fetch_table(conn, "triples", "novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number)))}
        ids.update(row["triple_id"] for row in self._fetch_table(conn, "triple_more_chapters", "novel_id = ? AND chapter_number = ?", (novel_id, int(chapter_number))))
        if story_node_id:
            ids.update(row["triple_id"] for row in self._fetch_table(conn, "triple_provenance", "novel_id = ? AND story_node_id = ?", (novel_id, story_node_id)))
            ids.update(row["triple_id"] for row in self._fetch_table(conn, "triple_attr", "attr_key = 'source_story_node_id' AND attr_value = ?", (story_node_id,)))
        return sorted(ids)

    def _fetch_one_table(self, conn, table: str, where: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
        rows = self._fetch_table(conn, table, where, params)
        return rows[0] if rows else None

    def _fetch_table(self, conn, table: str, where: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        if not self._table_exists(conn, table):
            return []
        return [dict(row) for row in conn.execute(f"SELECT * FROM {table} WHERE {where}", params).fetchall()]

    def _insert_rows(self, conn, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        primary_keys = self._primary_key_columns(conn, table)
        for row in rows:
            columns = list(row.keys())
            placeholders = ", ".join("?" for _ in columns)
            if primary_keys and all(key in columns for key in primary_keys):
                update_columns = [column for column in columns if column not in primary_keys]
                if update_columns:
                    assignments = ", ".join(f"{column} = excluded.{column}" for column in update_columns)
                    sql = (
                        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
                        f"ON CONFLICT({', '.join(primary_keys)}) DO UPDATE SET {assignments}"
                    )
                else:
                    sql = (
                        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
                        f"ON CONFLICT({', '.join(primary_keys)}) DO NOTHING"
                    )
                conn.execute(sql, tuple(row[col] for col in columns))
            else:
                conn.execute(
                    f"INSERT OR IGNORE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                    tuple(row[col] for col in columns),
                )

    def _delete_by_ids(self, conn, table: str, column: str, ids: list[str]) -> None:
        if not ids or not self._table_exists(conn, table):
            return
        placeholders = ",".join("?" for _ in ids)
        conn.execute(f"DELETE FROM {table} WHERE {column} IN ({placeholders})", tuple(ids))

    def _in_clause(self, column: str, ids: list[str], fallback: str) -> str:
        if not ids:
            return fallback
        return f"{column} IN ({','.join('?' for _ in ids)})"

    def _table_exists(self, conn, table: str) -> bool:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
            (table,),
        ).fetchone() is not None

    def _table_columns(self, conn, table: str) -> set[str]:
        if not self._table_exists(conn, table):
            return set()
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}

    def _primary_key_columns(self, conn, table: str) -> list[str]:
        if not self._table_exists(conn, table):
            return []
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return [row[1] for row in sorted((row for row in rows if row[5]), key=lambda row: row[5])]
