"""Pydantic schemas for the Miroir recommendation API."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

VALID_OCCASIONS = ["bureau", "cocktail", "vacances", "sport", "soiree", "casual"]
OccasionType = Literal["bureau", "cocktail", "vacances", "sport", "soiree", "casual"]


class RecommendRequest(BaseModel):
    client_id: str = Field(..., min_length=1, max_length=64)
    occasion: OccasionType
    k: int = Field(default=5, ge=1, le=20)
    exclude_ids: List[str] = Field(default_factory=list)


class ItemReco(BaseModel):
    item_id: str
    score: float
    article_type: Optional[str] = None
    base_colour: Optional[str] = None
    usage: Optional[str] = None
    image_url: Optional[str] = None


class RecommendResponse(BaseModel):
    client_id: str
    occasion: str
    items: List[ItemReco]


class HealthResponse(BaseModel):
    status: str
    model_version: Optional[str] = None
    n_catalog_items: Optional[int] = None


class FeedbackRequest(BaseModel):
    client_id: str = Field(..., min_length=1, max_length=64)
    item_id: str = Field(..., min_length=1)
    occasion: OccasionType
    action: Literal["approved", "rejected"]
    score: Optional[float] = None
    model_version: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: int
    status: str = "recorded"
