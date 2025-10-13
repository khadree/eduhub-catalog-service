"""Enrollment schemas"""
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from app.models.enrollment import EnrollmentStatus


class EnrollmentBase(BaseModel):
    """Base enrollment schema"""

    student_id: int
    course_id: int


class EnrollmentCreate(EnrollmentBase):
    """Schema for creating an enrollment"""

    enrollment_date: Optional[date] = None


class EnrollmentResponse(EnrollmentBase):
    """Schema for enrollment response"""

    id: int
    enrollment_date: date
    status: EnrollmentStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    student_name: Optional[str] = None
    course_title: Optional[str] = None

    class Config:
        from_attributes = True


class EnrollmentListResponse(BaseModel):
    """Schema for enrollment list response with pagination"""

    enrollments: List[EnrollmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
