"""Request and response contracts."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


Status = Literal["todo", "doing", "done"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: Status = "todo"
    priority: int = Field(default=3, ge=1, le=5)
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def nonblank_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title cannot be blank")
        return value


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: Status | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def nonblank_title(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("title cannot be blank")
        return value.strip() if value is not None else None


class Task(TaskCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class TaskPage(BaseModel):
    items: list[Task]
    total: int
    limit: int
    offset: int
