"""Student schemas"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional


class StudentBase(BaseModel):
    """Base student schema"""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    student_number: str = Field(..., min_length=1, max_length=50)
    grade_level: int = Field(..., ge=7, le=12)  # 7-12 for secondary school
    date_of_birth: Optional[date] = None


class StudentCreate(StudentBase):
    """Schema for creating a student"""

    user_id: str = Field(..., min_length=1, max_length=100)


class StudentUpdate(BaseModel):
    """Schema for updating a student"""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    grade_level: Optional[int] = Field(None, ge=7, le=12)
    date_of_birth: Optional[date] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    """Schema for student response"""

    id: int
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
