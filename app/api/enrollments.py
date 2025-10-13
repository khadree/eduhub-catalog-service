"""Enrollment endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import date

from app.database import get_db
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
    EnrollmentListResponse,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.course import Course
from app.models.student import Student
from app.middleware.auth import get_current_user, CurrentUser, UserRole
from app.cache import cache, get_cache_key

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


def serialize_enrollment(enrollment: Enrollment) -> dict:
    """Serialize enrollment model to dict for response"""
    return {
        "id": enrollment.id,
        "student_id": enrollment.student_id,
        "course_id": enrollment.course_id,
        "enrollment_date": enrollment.enrollment_date.isoformat(),
        "status": enrollment.status.value,
        "is_active": enrollment.is_active,
        "created_at": enrollment.created_at.isoformat(),
        "updated_at": enrollment.updated_at.isoformat(),
        "student_name": enrollment.student.full_name if enrollment.student else None,
        "course_title": enrollment.course.title if enrollment.course else None,
    }


@router.post("/", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_student(
    enrollment_data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Enroll a student in a course"""
    # Check if student exists
    result = await db.execute(
        select(Student).where(Student.id == enrollment_data.student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # Check if course exists
    result = await db.execute(
        select(Course).where(Course.id == enrollment_data.course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    # Check if course is active and published
    if not course.is_active or course.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course is not available for enrollment",
        )

    # Check if course is full
    if course.is_full:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course is full",
        )

    # Check if student is already enrolled
    result = await db.execute(
        select(Enrollment).where(
            and_(
                Enrollment.student_id == enrollment_data.student_id,
                Enrollment.course_id == enrollment_data.course_id,
            )
        )
    )
    existing_enrollment = result.scalar_one_or_none()
    if existing_enrollment:
        if existing_enrollment.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is already enrolled in this course",
            )
        else:
            # Reactivate enrollment
            existing_enrollment.is_active = True
            existing_enrollment.status = EnrollmentStatus.ACTIVE
            existing_enrollment.enrollment_date = (
                enrollment_data.enrollment_date or date.today()
            )
            await db.commit()
            await db.refresh(existing_enrollment)
            await db.refresh(existing_enrollment, ["student", "course"])

            # Invalidate cache
            await cache.delete_pattern("enrollments:*")
            await cache.delete_pattern("courses:*")

            return serialize_enrollment(existing_enrollment)

    # Create enrollment
    enrollment = Enrollment(
        student_id=enrollment_data.student_id,
        course_id=enrollment_data.course_id,
        enrollment_date=enrollment_data.enrollment_date or date.today(),
        status=EnrollmentStatus.ACTIVE,
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)

    # Eagerly load relationships
    await db.refresh(enrollment, ["student", "course"])

    # Invalidate cache
    await cache.delete_pattern("enrollments:*")
    await cache.delete_pattern("courses:*")

    return serialize_enrollment(enrollment)


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unenroll_student(
    enrollment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Unenroll a student from a course"""
    # Get enrollment
    result = await db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found"
        )

    # Mark as inactive and update status
    enrollment.is_active = False
    enrollment.status = EnrollmentStatus.DROPPED

    await db.commit()

    # Invalidate cache
    await cache.delete_pattern("enrollments:*")
    await cache.delete_pattern("courses:*")

    return None


@router.get("/", response_model=EnrollmentListResponse)
async def list_enrollments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    status_filter: Optional[EnrollmentStatus] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List enrollments with pagination and filters"""
    # Try to get from cache
    cache_key = get_cache_key(
        "enrollments", "list", page, page_size, student_id, course_id, status_filter, is_active
    )
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data

    # Build query
    query = select(Enrollment).join(Student).join(Course)

    # Apply filters
    if student_id:
        query = query.where(Enrollment.student_id == student_id)
    if course_id:
        query = query.where(Enrollment.course_id == course_id)
    if status_filter:
        query = query.where(Enrollment.status == status_filter)
    if is_active is not None:
        query = query.where(Enrollment.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    enrollments = result.scalars().all()

    # Serialize enrollments
    serialized_enrollments = [serialize_enrollment(enrollment) for enrollment in enrollments]

    response_data = {
        "enrollments": serialized_enrollments,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }

    # Cache the result
    await cache.set(cache_key, response_data)

    return response_data


@router.get("/course/{course_id}/students", response_model=EnrollmentListResponse)
async def list_enrolled_students(
    course_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all students enrolled in a specific course (for teachers)"""
    # Verify course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    # Try to get from cache
    cache_key = get_cache_key("enrollments", "course", course_id, page, page_size)
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data

    # Build query
    query = (
        select(Enrollment)
        .join(Student)
        .join(Course)
        .where(
            and_(
                Enrollment.course_id == course_id,
                Enrollment.is_active == True,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
    )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    enrollments = result.scalars().all()

    # Serialize enrollments
    serialized_enrollments = [serialize_enrollment(enrollment) for enrollment in enrollments]

    response_data = {
        "enrollments": serialized_enrollments,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }

    # Cache the result
    await cache.set(cache_key, response_data)

    return response_data


@router.get("/{enrollment_id}", response_model=EnrollmentResponse)
async def get_enrollment(
    enrollment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific enrollment by ID"""
    # Try to get from cache
    cache_key = get_cache_key("enrollments", "detail", enrollment_id)
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data

    # Get enrollment from database
    result = await db.execute(
        select(Enrollment)
        .where(Enrollment.id == enrollment_id)
        .join(Student)
        .join(Course)
    )
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found"
        )

    serialized_enrollment = serialize_enrollment(enrollment)

    # Cache the result
    await cache.set(cache_key, serialized_enrollment)

    return serialized_enrollment
