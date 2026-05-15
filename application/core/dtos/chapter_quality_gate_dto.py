"""Chapter quality gate DTOs."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class ChapterGateIssueDTO:
    code: str
    severity: str
    message: str
    action: str = ""


@dataclass
class ChapterQualityGateDTO:
    novel_id: str
    chapter_number: int
    gate_status: str
    chapter_status: str
    review_status: str
    can_enter_next: bool
    can_lock: bool
    word_count: int
    issues: List[ChapterGateIssueDTO] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ChapterIssueTaskDTO:
    id: str
    source: str
    code: str
    severity: str
    title: str
    evidence: str = ""
    basis: str = ""
    confidence: float = 1.0
    recommended_action: str = ""


@dataclass
class ChapterPreflightDTO:
    novel_id: str
    chapter_number: int
    outline_source: str
    selected_outline: str
    authority_lock: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    hard_conflicts: List[str] = field(default_factory=list)
    selected_authority: List[str] = field(default_factory=list)
