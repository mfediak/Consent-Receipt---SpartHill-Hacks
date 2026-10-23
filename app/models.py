from typing import Literal
from pydantic import BaseModel, Field

Category = Literal[
    "data_collection", "data_usage", "data_sharing", "user_rights", "data_retention"
]
CATEGORIES: list[str] = list(Category.__args__)


class Disclosure(BaseModel):
    category: Category
    summary: str = Field(description="One or two plain-English sentences, under 40 words.")
    evidence: str = Field(description="Exact contiguous quote copied from the policy, or empty.")
    status: Literal["disclosed", "unclear", "not_found"]


class PolicyAnalysis(BaseModel):
    company: str = Field(description="Company name from the policy, or 'Unknown'.")
    overview: str = Field(description="Neutral two-sentence overview, under 50 words.")
    disclosures: list[Disclosure]
