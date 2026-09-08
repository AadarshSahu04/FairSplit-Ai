"""
Pydantic model for Person.
"""
from pydantic import BaseModel, Field


class Person(BaseModel):
    """A diner whose share will be calculated."""

    id: str = Field(..., description="UUID — stable even with duplicate names")
    name: str = Field(..., min_length=1, description="Display name for the person")
