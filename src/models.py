"""Output schema the Gemini API must follow (structured output)."""

from typing import Literal

from pydantic import BaseModel, Field

CategoryKey = Literal[
    "data_collection",
    "data_usage",
    "data_sharing",
    "user_rights",
    "data_retention",
]


class Disclosure(BaseModel):
    # Field order matters: the model writes the quote first, then summarizes it,
    # then picks a status. Summarizing from a quote it just copied keeps the
    # summary closer to the policy's own words.
    category: CategoryKey
    evidence: str = Field(
        description=(
            "One passage copied character for character from the policy. "
            "Empty string when status is not_found."
        )
    )
    summary: str = Field(
        description="One or two sentences in simple, neutral English."
    )
    status: Literal["disclosed", "unclear", "not_found"]


class PolicyAnalysis(BaseModel):
    disclosures: list[Disclosure]
