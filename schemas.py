from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, model_validator

# Text fields are trimmed, so "   " counts as empty and is rejected
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class TaskCreate(BaseModel):
    title: Title
    description: Description
    completed: bool = False


class TaskUpdate(BaseModel):
    """Partial update: only the fields that are sent are changed."""
    title: Title | None = None
    description: Description | None = None
    completed: bool | None = None

    @model_validator(mode="after")
    def reject_nulls_and_empty_updates(self):
        sent = self.model_fields_set
        if not sent:
            raise ValueError("Send at least one field to update")
        for field in sent:
            if getattr(self, field) is None:
                raise ValueError(f"'{field}' cannot be null")
        return self


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskPage(BaseModel):
    """One page of tasks plus the information needed to fetch the next page."""
    items: list[TaskResponse]
    total: int
    limit: int
    offset: int


class UserCreate(BaseModel):
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50)]
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
