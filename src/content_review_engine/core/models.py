from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]


class ReviewIssue(BaseModel):
    id: str
    severity: Severity
    category: str
    title: str
    description: str
    suggestion: str
    original_text: str | None = None
    start_line: int | None = None
    end_line: int | None = None


class ReviewResult(BaseModel):
    document_id: str
    profile_name: str
    overall_score: float = Field(ge=0, le=100)
    summary: str
    issues: list[ReviewIssue]
    rewritten_markdown: str | None = None
    diff: str | None = None


class ReviewProfile(BaseModel):
    name: str
    target_platform: str
    tone: str = "clear and professional"
    max_title_length: int = 32
    max_paragraph_length: int = 220


__all__ = [
    "ReviewIssue",
    "ReviewProfile",
    "ReviewResult",
    "Severity",
]
