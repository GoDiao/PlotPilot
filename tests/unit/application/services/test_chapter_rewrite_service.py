from pathlib import Path

from application.core.services.chapter_rewrite_service import ChapterRewriteService
from infrastructure.persistence.database.connection import DatabaseConnection


def _db(tmp_path: Path) -> DatabaseConnection:
    return DatabaseConnection(str(tmp_path / "rewrite-test.db"))


def _seed_base(db: DatabaseConnection, novel_id: str = "novel-rewrite") -> None:
    conn = db.get_connection()
    conn.execute(
        "INSERT INTO novels (id, title, slug, target_chapters) VALUES (?, ?, ?, ?)",
        (novel_id, "Rewrite Test", novel_id, 3),
    )
    conn.execute(
        """
        INSERT INTO chapters (id, novel_id, number, title, content, outline, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("chapter-1", novel_id, 1, "Chapter 1", "old content", "outline", "completed"),
    )
    conn.execute(
        """
        INSERT INTO chapters (id, novel_id, number, title, content, outline, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("chapter-2", novel_id, 2, "Chapter 2", "later content", "outline", "completed"),
    )
    conn.execute(
        "INSERT INTO knowledge (id, novel_id, premise_lock) VALUES (?, ?, ?)",
        ("knowledge-1", novel_id, "locked premise"),
    )
    conn.commit()


def _fetch(db: DatabaseConnection, sql: str, params: tuple = ()) -> dict | None:
    return db.fetch_one(sql, params)


def test_soft_reset_clears_only_chapter_scoped_side_effects(tmp_path):
    db = _db(tmp_path)
    novel_id = "novel-soft"
    _seed_base(db, novel_id)
    conn = db.get_connection()
    conn.execute(
        "INSERT INTO chapter_summaries (id, knowledge_id, chapter_number, summary) VALUES (?, ?, ?, ?)",
        ("summary-1", "knowledge-1", 1, "polluted summary"),
    )
    conn.execute(
        "INSERT INTO narrative_events (event_id, novel_id, chapter_number, event_summary) VALUES (?, ?, ?, ?)",
        ("event-1", novel_id, 1, "polluted event"),
    )
    conn.execute(
        "INSERT INTO novel_foreshadow_registry (novel_id, payload) VALUES (?, ?)",
        (novel_id, '{"global":"keep"}'),
    )
    conn.execute(
        "INSERT INTO bible_characters (id, novel_id, name, description) VALUES (?, ?, ?, ?)",
        ("char-1", novel_id, "Keep Me", "global bible"),
    )
    conn.commit()

    result = ChapterRewriteService(db).reset_for_rewrite(novel_id, 1)

    assert result["mode"] == "soft_reset"
    assert result["warnings"]
    chapter = _fetch(db, "SELECT content, status FROM chapters WHERE novel_id = ? AND number = 1", (novel_id,))
    assert chapter == {"content": "", "status": "draft"}
    assert _fetch(db, "SELECT * FROM chapter_summaries WHERE id = 'summary-1'") is None
    assert _fetch(db, "SELECT * FROM narrative_events WHERE event_id = 'event-1'") is None
    assert _fetch(db, "SELECT payload FROM novel_foreshadow_registry WHERE novel_id = ?", (novel_id,))["payload"] == '{"global":"keep"}'
    assert _fetch(db, "SELECT name FROM bible_characters WHERE id = 'char-1'")["name"] == "Keep Me"


def test_snapshot_restore_reverts_global_side_effects_and_clears_chapter(tmp_path):
    db = _db(tmp_path)
    novel_id = "novel-snapshot"
    _seed_base(db, novel_id)
    conn = db.get_connection()
    conn.execute(
        "INSERT INTO novel_foreshadow_registry (novel_id, payload) VALUES (?, ?)",
        (novel_id, '{"before":true}'),
    )
    conn.execute(
        "INSERT INTO bibles (id, novel_id) VALUES (?, ?)",
        ("bible-1", novel_id),
    )
    conn.execute(
        "INSERT INTO bible_characters (id, novel_id, name, description) VALUES (?, ?, ?, ?)",
        ("char-1", novel_id, "Original", "before"),
    )
    conn.execute(
        "INSERT INTO bible_character_relationships (id, character_id, target_name, relation) VALUES (?, ?, ?, ?)",
        ("rel-1", "char-1", "Ally", "before"),
    )
    conn.execute(
        "INSERT INTO triples (id, novel_id, subject, predicate, object, chapter_number) VALUES (?, ?, ?, ?, ?, ?)",
        ("triple-1", novel_id, "A", "knows", "B", 1),
    )
    conn.execute(
        "INSERT INTO triple_attr (triple_id, attr_key, attr_value) VALUES (?, ?, ?)",
        ("triple-1", "source", "before"),
    )
    conn.commit()

    service = ChapterRewriteService(db)
    snapshot = service.create_prewrite_snapshot(novel_id, 1, "test")
    assert snapshot["id"]

    conn.execute("UPDATE chapters SET content = ?, status = ? WHERE novel_id = ? AND number = 1", ("new content", "completed", novel_id))
    conn.execute("UPDATE novel_foreshadow_registry SET payload = ? WHERE novel_id = ?", ('{"after":true}', novel_id))
    conn.execute("UPDATE bible_characters SET name = ? WHERE id = ?", ("Polluted", "char-1"))
    conn.execute(
        "INSERT INTO bible_characters (id, novel_id, name, description) VALUES (?, ?, ?, ?)",
        ("char-2", novel_id, "Pollution", "after"),
    )
    conn.execute(
        "INSERT INTO chapter_summaries (id, knowledge_id, chapter_number, summary) VALUES (?, ?, ?, ?)",
        ("summary-after", "knowledge-1", 1, "after summary"),
    )
    conn.execute(
        "INSERT INTO triples (id, novel_id, subject, predicate, object, chapter_number) VALUES (?, ?, ?, ?, ?, ?)",
        ("triple-2", novel_id, "X", "pollutes", "Y", 1),
    )
    conn.commit()

    result = service.reset_for_rewrite(novel_id, 1)

    assert result["mode"] == "snapshot_restore"
    chapter = _fetch(db, "SELECT content, status FROM chapters WHERE novel_id = ? AND number = 1", (novel_id,))
    assert chapter == {"content": "", "status": "draft"}
    assert _fetch(db, "SELECT payload FROM novel_foreshadow_registry WHERE novel_id = ?", (novel_id,))["payload"] == '{"before":true}'
    assert _fetch(db, "SELECT name FROM bible_characters WHERE id = 'char-1'")["name"] == "Original"
    assert _fetch(db, "SELECT * FROM bible_characters WHERE id = 'char-2'") is None
    assert _fetch(db, "SELECT * FROM chapter_summaries WHERE id = 'summary-after'") is None
    assert _fetch(db, "SELECT * FROM triples WHERE id = 'triple-1'") is not None
    assert _fetch(db, "SELECT * FROM triple_attr WHERE triple_id = 'triple-1'") is not None
    assert _fetch(db, "SELECT * FROM triples WHERE id = 'triple-2'") is None
    assert _fetch(db, "SELECT status FROM chapter_rewrite_snapshots WHERE id = ?", (snapshot["id"],))["status"] == "restored"


def test_preview_warns_when_later_completed_chapters_exist(tmp_path):
    db = _db(tmp_path)
    novel_id = "novel-warning"
    _seed_base(db, novel_id)

    preview = ChapterRewriteService(db).preview_reset(novel_id, 1)

    assert preview["mode"] == "soft_reset"
    assert any("1" in warning for warning in preview["warnings"])
