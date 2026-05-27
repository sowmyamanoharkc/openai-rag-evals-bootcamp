"""Reference solution: Pydantic models for meeting-notes extraction."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Attendee(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Full name as it appeared in the transcript.")
    email: str | None = Field(default=None, description="Acme email if known, else null.")
    team: str | None = Field(default=None, description="Team name if known, else null.")


class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: str = Field(description="Must match an attendee.name exactly.")
    task: str = Field(description="What the owner committed to do.")
    due: str | None = Field(
        default=None,
        description="ISO date YYYY-MM-DD if mentioned, else null. Do not invent dates.",
    )


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(description="A concrete decision the meeting reached.")


class MeetingNotes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    attendees: list[Attendee]
    decisions: list[Decision]
    action_items: list[ActionItem]

    @model_validator(mode="after")
    def _owners_must_be_attendees(self) -> "MeetingNotes":
        attendee_names = {a.name for a in self.attendees}
        for item in self.action_items:
            if item.owner not in attendee_names:
                raise ValueError(
                    f"Unknown action_item owner: {item.owner!r}. "
                    f"Owners must match one of the attendee names exactly: "
                    f"{sorted(attendee_names)}"
                )
        return self
