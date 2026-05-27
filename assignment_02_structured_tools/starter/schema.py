"""Pydantic models for meeting-notes extraction.

These models are the contract between the model and your code. The OpenAI
Structured Outputs API will be told to produce JSON that conforms to the schema
generated from `MeetingNotes`.

You must complete every TODO. Do not change the public model names.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Attendee(BaseModel):
    """A person who attended the meeting.

    TODO:
      - Set model_config = ConfigDict(extra="forbid").
        (Structured Outputs requires additionalProperties: false on every object.)
      - Define fields:
          name:  str            (required)
          email: str | None = None
          team:  str | None = None
      - Add Field(description=...) on each so the model knows what to put there.
    """
    # TODO: model_config and fields go here.
    pass


class ActionItem(BaseModel):
    """A specific task an attendee committed to.

    TODO:
      - Set model_config = ConfigDict(extra="forbid").
      - Define fields:
          owner: str               (must match an attendee.name; enforced by MeetingNotes)
          task:  str
          due:   str | None = None ISO date "YYYY-MM-DD" or None
    """
    pass


class Decision(BaseModel):
    """A single decision recorded in the meeting.

    TODO:
      - Set model_config = ConfigDict(extra="forbid").
      - Define field:
          text: str
    """
    pass


class MeetingNotes(BaseModel):
    """The full extracted notes object.

    TODO:
      - Set model_config = ConfigDict(extra="forbid").
      - Define fields:
          title:        str
          attendees:    list[Attendee]
          decisions:    list[Decision]
          action_items: list[ActionItem]

      - Add a @model_validator(mode="after") that enforces:
          every action_item.owner must match exactly one attendee.name.
        If not, raise ValueError(f"Unknown action_item owner: {owner!r} ...").
        This is the rule the retry loop will exercise.
    """
    pass
