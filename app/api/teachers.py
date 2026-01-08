"""Teacher endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.sql import Select
from typing import List

from app.database import get_db
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherResponse
from app.models.teacher import Teacher
from app.middleware.auth import get_current_user, CurrentUser, UserRole

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_data: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new teacher (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create teachers",
        )

    result = await db.execute(
        select(Teacher).where(
            (Teacher.user_id == teacher_data.user_id)
            | (Teacher.email == teacher_data.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher with this user_id or email already exists",
        )

    teacher = Teacher(**teacher_data.model_dump())
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)

    return teacher


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific teacher by ID"""
    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalar_one_or_none()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    return teacher


@router.get("/", response_model=List[TeacherResponse]) 
async def get_teachers(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search in name or email"),
    specialization: str | None = Query(None, description="Filter by specialization"),
):
    """
    Get list of all teachers with pagination and optional filters.
    """
    query: Select = select(Teacher)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Teacher.first_name).like(search_term),
                func.lower(Teacher.last_name).like(search_term),
                func.lower(Teacher.email).like(search_term),
            )
        )
    if specialization:
        query = query.where(
            Teacher.specialization.ilike(f"%{specialization}%")
        )
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * limit
    query = query.order_by(Teacher.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    teachers = result.scalars().all()


    return teachers


@router.get("/check-exists/{email}", response_model=bool)
async def check_teacher_exists(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Check if a teacher profile exists by email"""
    result = await db.execute(
        select(Teacher).where(func.lower(Teacher.email) == email.lower())
    )
    teacher = result.scalar_one_or_none()
    return teacher is not None