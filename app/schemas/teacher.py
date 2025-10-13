"""Teacher schemas"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class TeacherBase(BaseModel):
    """Base teacher schema"""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    bio: Optional[str] = None
    specialization: Optional[str] = Field(None, max_length=200)


class TeacherCreate(TeacherBase):
    """Schema for creating a teacher"""

    user_id: str = Field(..., min_length=1, max_length=100)


class TeacherUpdate(BaseModel):
    """Schema for updating a teacher"""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    specialization: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class TeacherResponse(TeacherBase):
    """Schema for teacher response"""

    id: int
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
