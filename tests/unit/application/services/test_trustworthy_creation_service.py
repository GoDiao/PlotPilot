import asyncio

from application.core.services.trustworthy_creation_service import TrustworthyCreationService


class FakeDb:
    def __init__(self):
        self.memory = {}
        self.actions = {}
        self.drafts = {}
        self.snapshots = {}

    def execute(self, sql, params=()):
        if "INSERT INTO chapter_memory_entries" in sql:
            self.memory[params[0]] = {
                "id": params[0],
                "novel_id": params[1],
                "chapter_number": params[2],
                "memory_layer": params[3],
                "source": params[4],
                "entry_type": params[5],
                "content": params[6],
                "payload": params[7],
                "issue_id": params[8],
                "status": "active",
            }
        elif "UPDATE chapter_memory_entries" in sql:
            self.memory[params[1]]["memory_layer"] = params[0]
        elif "INSERT INTO chapter_issue_actions" in sql:
            self.actions[params[0]] = {
                "id": params[0],
                "novel_id": params[1],
                "chapter_number": params[2],
                "issue_id": params[3],
                "action": params[4],
                "memo": params[5],
            }
        elif "INSERT INTO chapter_snapshots" in sql:
            self.snapshots[params[0]] = {
                "id": params[0],
                "novel_id": params[1],
                "chapter_number": params[2],
                "content": params[3],
                "reason": params[4],
            }
        elif "INSERT INTO chapter_revision_drafts" in sql:
            self.drafts[params[0]] = {
                "id": params[0],
                "novel_id": params[1],
                "chapter_number": params[2],
                "source": "tension",
                "variant_label": params[3],
                "original_content": params[4],
                "revised_content": params[5],
                "diff_text": params[6],
                "status": "draft",
            }
        elif "UPDATE chapter_revision_drafts" in sql:
            self.drafts[params[0]]["status"] = "applied"
        return None

    def commit(self):
        return None

    def fetch_one(self, sql, params=()):
        if "chapter_memory_entries" in sql:
            return self.memory.get(params[0])
        if "chapter_issue_actions" in sql:
            return self.actions.get(params[0])
        if "chapter_revision_drafts" in sql:
            return self.drafts.get(params[0])
        if "chapter_snapshots" in sql:
            rows = [row for row in self.snapshots.values() if row["novel_id"] == params[0] and row["chapter_number"] == params[1]]
            return rows[-1] if rows else None
        return None

    def fetch_all(self, sql, params=()):
        if "chapter_memory_entries" in sql:
            return list(self.memory.values())
        if "chapter_revision_drafts" in sql:
            return list(self.drafts.values())
        return []


class FakeChapter:
    def __init__(self, content):
        self.content = content


class FakeChapterService:
    def __init__(self):
        self.content = "原文第一行\n原文第二行"

    def get_chapter_by_novel_and_number(self, novel_id, chapter_number):
        return FakeChapter(self.content)

    def update_chapter_by_novel_and_number(self, novel_id, chapter_number, content):
        self.content = content
        return {"content": content}


def test_memory_entry_can_promote_to_canonical():
    service = TrustworthyCreationService(FakeDb(), FakeChapterService())

    entry = service.add_memory_entry("novel-1", 1, "pending", "test", "fact", "李维是主角")
    promoted = service.promote_memory_entry(entry["id"])

    assert promoted["memory_layer"] == "canonical"
    assert promoted["content"] == "李维是主角"


def test_issue_action_accept_new_setting_creates_pending_memory():
    db = FakeDb()
    service = TrustworthyCreationService(db, FakeChapterService())

    action = service.apply_issue_action("novel-1", 1, "issue-1", "accept_new_setting", "接受林远为新角色")

    assert action["action"] == "accept_new_setting"
    assert any(row["memory_layer"] == "pending" for row in db.memory.values())


def test_revision_draft_can_apply_and_rollback():
    chapter_service = FakeChapterService()
    service = TrustworthyCreationService(FakeDb(), chapter_service)

    drafts = asyncio.run(service.create_tension_revision_drafts("novel-1", 1, {"suggestions": ["增加冲突"]}))
    result = service.apply_revision_draft(drafts[0]["id"])

    assert result["draft"]["status"] == "applied"
    assert "修订提示" in chapter_service.content
    rollback = service.rollback_latest_snapshot("novel-1", 1)
    assert rollback["chapter"]["content"] == "原文第一行\n原文第二行"
