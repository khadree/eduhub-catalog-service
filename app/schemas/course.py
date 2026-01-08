from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.course import CourseStatus


class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1, max_length=50)
    category_id: int
    teacher_id: int
    max_students: int = Field(default=30, ge=1)
    duration_weeks: int = Field(..., ge=1)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    category_id: Optional[int] = None
    teacher_id: Optional[int] = None
    max_students: Optional[int] = Field(None, ge=1)
    duration_weeks: Optional[int] = Field(None, ge=1)
    status: Optional[CourseStatus] = None
    is_active: Optional[bool] = None


class CourseCreateResponse(BaseModel):
    """Response specifically for newly created courses — no ORM properties accessed"""
    id: int
    title: str
    description: str
    code: str
    category_id: int
    teacher_id: int
    max_students: int
    duration_weeks: int
    status: CourseStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    teacher_name: Optional[str] = None
    category_name: Optional[str] = None

    # Always 0 and False for new courses
    enrolled_count: int = 0
    is_full: bool = False

    model_config = ConfigDict(from_attributes=True)  # Still allowed — we manually populate safe fields


class CourseResponse(CourseBase):
    id: int
    status: CourseStatus
    is_active: bool
    enrolled_count: int
    is_full: bool
    created_at: datetime
    updated_at: datetime
    teacher_name: Optional[str] = None
    category_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourseListResponse(BaseModel):
    courses: List[CourseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int