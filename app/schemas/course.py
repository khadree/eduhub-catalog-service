"""Course schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.course import CourseStatus


class CourseBase(BaseModel):
    """Base course schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1, max_length=50)
    category_id: int
    teacher_id: int
    max_students: int = Field(default=30, ge=1)
    duration_weeks: int = Field(..., ge=1)


class CourseCreate(CourseBase):
    """Schema for creating a course"""

    pass


class CourseUpdate(BaseModel):
    """Schema for updating a course"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    category_id: Optional[int] = None
    teacher_id: Optional[int] = None
    max_students: Optional[int] = Field(None, ge=1)
    duration_weeks: Optional[int] = Field(None, ge=1)
    status: Optional[CourseStatus] = None
    is_active: Optional[bool] = None


class CourseResponse(CourseBase):
    """Schema for course response"""

    id: int
    status: CourseStatus
    is_active: bool
    enrolled_count: int
    is_full: bool
    created_at: datetime
    updated_at: datetime
    teacher_name: Optional[str] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    """Schema for course list response with pagination"""

    courses: List[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
