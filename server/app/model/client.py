from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_PEOPLE = {"Sumit", "Shree", "Abhishek"}


class ClientFirestoreModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=200)
    category: Literal[
        "Display Only",
        "Portfolio — Basic Contact Form",
        "Portfolio — WhatsApp Lead Integration",
        "Management System — Backend + DB",
    ]
    description: str = ""
    cost: int = Field(..., ge=0)
    status: Literal["Open", "In progress", "Review", "Completed"] = "Open"
    due: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    designUrl: Optional[str] = None
    codeUrl: Optional[str] = None
    people: list[str] = Field(..., min_length=2, max_length=3)
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty or whitespace.")
        return cleaned

    @field_validator("due")
    @classmethod
    def validate_due(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Due date must be in YYYY-MM-DD format.") from exc
        return value

    @field_validator("people")
    @classmethod
    def validate_people(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("people cannot be empty")

        cleaned: list[str] = []
        seen: set[str] = set()

        for person in value:
            person = person.strip()
            if not person:
                continue

            if person not in VALID_PEOPLE:
                raise ValueError(f"invalid team member: {person}")

            if person in seen:
                raise ValueError(f"duplicate person in people: {person}")

            seen.add(person)
            cleaned.append(person)

        if "Sumit" not in cleaned or "Shree" not in cleaned:
            raise ValueError("people must always include Sumit and Shree")

        if len(cleaned) > 3:
            raise ValueError("people can contain at most Sumit, Shree, and Abhishek")

        return cleaned

    @field_validator("designUrl", "codeUrl")
    @classmethod
    def validate_optional_urls(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value.strip():
            return None
        return value.strip()

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict[str, Any]) -> "ClientFirestoreModel":
        payload = dict(data)
        payload["id"] = doc_id

        for field_name in ["createdAt", "updatedAt", "completedAt"]:
            value = payload.get(field_name)
            if isinstance(value, str) and value:
                try:
                    payload[field_name] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    pass

        return cls.model_validate(payload)

    def to_firestore(self) -> dict[str, Any]:
        payload = self.model_dump(
            mode="python",
            exclude_none=True,
            exclude={"id"},
        )
        return payload


class ClientCreateRequest(ClientFirestoreModel):
    id: Optional[str] = None


class ClientUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    category: Optional[
        Literal[
            "Display Only",
            "Portfolio — Basic Contact Form",
            "Portfolio — WhatsApp Lead Integration",
            "Management System — Backend + DB",
        ]
    ] = None
    description: Optional[str] = None
    cost: Optional[int] = Field(default=None, ge=0)
    status: Optional[Literal["Open", "In progress", "Review", "Completed"]] = None
    due: Optional[str] = None
    designUrl: Optional[str] = None
    codeUrl: Optional[str] = None
    people: Optional[list[str]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty or whitespace.")
        return cleaned

    @field_validator("due")
    @classmethod
    def validate_due(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Due date must be in YYYY-MM-DD format.") from exc
        return value

    @field_validator("people")
    @classmethod
    def validate_people(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return value
        if not value:
            raise ValueError("people cannot be empty")

        cleaned: list[str] = []
        seen: set[str] = set()

        for person in value:
            person = person.strip()
            if not person:
                continue
            if person not in VALID_PEOPLE:
                raise ValueError(f"invalid team member: {person}")
            if person in seen:
                raise ValueError(f"duplicate person in people: {person}")
            seen.add(person)
            cleaned.append(person)

        if "Sumit" not in cleaned or "Shree" not in cleaned:
            raise ValueError("people must always include Sumit and Shree")

        return cleaned

    @field_validator("designUrl", "codeUrl")
    @classmethod
    def validate_optional_urls(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value.strip():
            return None
        return value.strip()