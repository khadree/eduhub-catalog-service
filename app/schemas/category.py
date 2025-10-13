"""Category schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CategoryBase(BaseModel):
    """Base category schema"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    slug: str = Field(..., min_length=1, max_length=100)


class CategoryCreate(CategoryBase):
    """Schema for creating a category"""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    slug: Optional[str] = Field(None, min_length=1, max_length=100)


class CategoryResponse(CategoryBase):
    """Schema for category response"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
