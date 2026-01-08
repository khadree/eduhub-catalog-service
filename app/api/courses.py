"""Course endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseCreateResponse,
    CourseListResponse,
)
from app.models.course import Course, CourseStatus
from app.models.teacher import Teacher
from app.models.category import Category
from app.middleware.auth import get_current_user, CurrentUser, UserRole
from app.cache import cache, get_cache_key
from app.config import settings

router = APIRouter(prefix="/courses", tags=["Courses"])


def serialize_course(course: Course, enrolled_count: Optional[int] = None) -> dict:
    """
    Safely serialize a Course instance for list/search/detail responses.
    enrolled_count is passed explicitly to avoid lazy loading enrollments.
    """
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "code": course.code,
        "category_id": course.category_id,
        "teacher_id": course.teacher_id,
        "max_students": course.max_students,
        "duration_weeks": course.duration_weeks,
        "status": course.status.value if isinstance(course.status, CourseStatus) else course.status,
        "is_active": course.is_active,
        "enrolled_count": enrolled_count if enrolled_count is not None else course.enrolled_count,
        "is_full": course.is_full,
        "created_at": course.created_at.isoformat(),
        "updated_at": course.updated_at.isoformat(),
        "teacher_name": getattr(course.teacher, "full_name", None) if hasattr(course, "teacher") and course.teacher else None,
        "category_name": getattr(course.category, "name", None) if hasattr(course, "category") and course.category else None,
    }


@router.post("/", response_model=CourseCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new course (Admin/Teacher only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can create courses",
        )

    # Check code uniqueness
    if await db.scalar(select(Course).where(Course.code == course_data.code)):
        raise HTTPException(status_code=400, detail="Course code already exists")

    # Validate foreign keys
    if not await db.scalar(select(Teacher).where(Teacher.id == course_data.teacher_id)):
        raise HTTPException(status_code=404, detail="Teacher not found")
    if not await db.scalar(select(Category).where(Category.id == course_data.category_id)):
        raise HTTPException(status_code=404, detail="Category not found")

    course = Course(**course_data.model_dump())
    db.add(course)
    await db.commit()
    await db.refresh(course)
    await db.refresh(course, ["teacher", "category"])

    await cache.delete_pattern("courses:*")

    # Manually construct safe response
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "code": course.code,
        "category_id": course.category_id,
        "teacher_id": course.teacher_id,
        "max_students": course.max_students,
        "duration_weeks": course.duration_weeks,
        "status": course.status,
        "is_active": course.is_active,
        "created_at": course.created_at,
        "updated_at": course.updated_at,
        "teacher_name": course.teacher.full_name if course.teacher else None,
        "category_name": course.category.name if course.category else None,
        "enrolled_count": 0,
        "is_full": False,
    }


@router.get("/", response_model=CourseListResponse)
async def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[CourseStatus] = None,
    category_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all courses with pagination and filters"""
    cache_key = get_cache_key(
        "courses", "list", page, page_size, status_filter, category_id, teacher_id, is_active
    )
    if cached_data := await cache.get(cache_key):
        return cached_data

    query = (
        select(Course)
        .join(Teacher)
        .join(Category)
        .options(
            selectinload(Course.teacher),
            selectinload(Course.category),
            selectinload(Course.enrollments),
        )
    )

    if status_filter:
        query = query.where(Course.status == status_filter)
    if category_id:
        query = query.where(Course.category_id == category_id)
    if teacher_id:
        query = query.where(Course.teacher_id == teacher_id)
    if is_active is not None:
        query = query.where(Course.is_active == is_active)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    courses = (await db.execute(query)).scalars().all()

    serialized_courses = [
        serialize_course(course, enrolled_count=course.enrolled_count)
        for course in courses
    ]

    response_data = {
        "courses": serialized_courses,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }

    await cache.set(cache_key, response_data, ttl=settings.cache_ttl)
    return response_data


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific course by ID"""
    cache_key = get_cache_key("courses", "detail", course_id)
    if cached_data := await cache.get(cache_key):
        return cached_data

    result = await db.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.teacher),
            selectinload(Course.category),
            selectinload(Course.enrollments),
        )
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    serialized_course = serialize_course(course, enrolled_count=course.enrolled_count)

    await cache.set(cache_key, serialized_course, ttl=settings.cache_ttl)
    return serialized_course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update a course (Admin/Teacher only)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and teachers can update courses",
        )

    result = await db.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.teacher),
            selectinload(Course.category),
            selectinload(Course.enrollments),
        )
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if course_data.code and course_data.code != course.code:
        if await db.scalar(select(Course).where(Course.code == course_data.code)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course code already exists",
            )

    update_data = course_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)

    await db.commit()
    await db.refresh(course)
    await db.refresh(course, ["teacher", "category"])

    await cache.delete_pattern("courses:*")

    return serialize_course(course, enrolled_count=course.enrolled_count)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a course (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete courses",
        )

    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    await db.delete(course)
    await db.commit()

    await cache.delete_pattern("courses:*")
    return None


@router.get("/search/", response_model=CourseListResponse)
async def search_courses(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search courses by title, code, or teacher name"""
    cache_key = get_cache_key("courses", "search", q, page, page_size)
    if cached_data := await cache.get(cache_key):
        return cached_data

    query = (
        select(Course)
        .join(Teacher)
        .join(Category)
        .options(
            selectinload(Course.teacher),
            selectinload(Course.category),
            selectinload(Course.enrollments),
        )
        .where(
            or_(
                Course.title.ilike(f"%{q}%"),
                Course.code.ilike(f"%{q}%"),
                Teacher.first_name.ilike(f"%{q}%"),
                Teacher.last_name.ilike(f"%{q}%"),
            )
        )
    )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    courses = (await db.execute(query)).scalars().all()

    serialized_courses = [
        serialize_course(course, enrolled_count=course.enrolled_count)
        for course in courses
    ]

    response_data = {
        "courses": serialized_courses,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }

    await cache.set(cache_key, response_data, ttl=settings.cache_ttl)
    return response_data