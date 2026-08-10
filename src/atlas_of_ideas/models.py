from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


Domain = Literal[
    "science",
    "philosophy",
    "history",
    "politics",
    "spirituality",
    "psychology",
    "literature",
    "other",
]

RelationKind = Literal[
    "semantic_similarity",
    "historical_influence",
    "analogy",
    "contradiction",
    "co_occurrence",
    "human_interpretation",
]

CandidateStatus = Literal["pending", "accepted", "rejected"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Workspace(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)


class SourceDocument(BaseModel):
    id: str
    workspace_id: str = "default"
    title: str
    author: str | None = None
    year: int | None = None
    domain: Domain = "other"
    text: str
    filename: str | None = None
    url: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)


class Passage(BaseModel):
    id: str
    workspace_id: str = "default"
    document_id: str
    text: str
    start_char: int
    end_char: int


class Concept(BaseModel):
    id: str
    workspace_id: str = "default"
    label: str
    domain: Domain = "other"
    aliases: list[str] = Field(default_factory=list)
    source_passage_ids: list[str] = Field(default_factory=list)
    extraction_method: str = "local_tfidf"
    user_validated: bool = False


class Evidence(BaseModel):
    passage_id: str
    quote: str
    source_title: str


class Relation(BaseModel):
    id: str | None = None
    workspace_id: str = "default"
    source_concept_id: str
    target_concept_id: str
    kind: RelationKind
    score: float = Field(ge=0, le=1)
    rationale: str
    evidence: list[Evidence] = Field(default_factory=list)
    proposed_by: str = "system"
    validated_by_user: bool = False
    created_at: str = Field(default_factory=utc_now_iso)


class CandidateRelation(BaseModel):
    id: str
    workspace_id: str = "default"
    source_concept_id: str
    target_concept_id: str
    suggested_kind: RelationKind = "semantic_similarity"
    semantic_score: float = Field(ge=0, le=1)
    rationale: str
    evidence: list[Evidence] = Field(default_factory=list)
    status: CandidateStatus = "pending"
    reviewed_kind: RelationKind | None = None
    created_at: str = Field(default_factory=utc_now_iso)
