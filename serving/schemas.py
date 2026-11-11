from enum import Enum
from pydantic import BaseModel, Field, field_validator


class AccessLevel(str, Enum):
    public = "public"
    support = "support"
    engineering = "engineering"


class QARequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    access_level: AccessLevel = AccessLevel.public

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question cannot be blank")
        return value


class Citation(BaseModel):
    document_id: str
    title: str
    chunk_id: str


class QAResponse(BaseModel):
    answer: str
    citations: list[Citation]
    refused: bool


class TriageRequest(BaseModel):
    ticket: str = Field(min_length=5, max_length=8000)


class TriageResponse(BaseModel):
    category: str
    priority: str
    product_area: str
    summary: str

    @field_validator("category")
    @classmethod
    def valid_category(cls, value: str) -> str:
        allowed = {"bug", "billing", "account", "feature_request", "how_to", "security", "other"}
        value = value.strip().lower()
        if value not in allowed:
            raise ValueError("invalid ticket category")
        return value

    @field_validator("priority")
    @classmethod
    def valid_priority(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in {"low", "normal", "high", "urgent"}:
            raise ValueError("invalid priority")
        return value

    @field_validator("summary")
    @classmethod
    def bounded_summary(cls, value: str) -> str:
        return " ".join(value.split())[:240]
