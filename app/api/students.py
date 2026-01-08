"""Student endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.sql import Select
from typing import List

from app.database import get_db
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.models.student import Student
from app.middleware.auth import get_current_user, CurrentUser, UserRole

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new student (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create students",
        )

    # Check if user_id, email, or student_number already exists
    result = await db.execute(
        select(Student).where(
            (Student.user_id == student_data.user_id)
            | (Student.email == student_data.email)
            | (Student.student_number == student_data.student_number)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student with this user_id, email, or student_number already exists",
        )

    student = Student(**student_data.model_dump())
    db.add(student)
    await db.commit()
    await db.refresh(student)

    return student


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific student by ID"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    return student


@router.get("/", response_model=List[StudentResponse]) 
async def get_students(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search in name or email"),
    specialization: str | None = Query(None, description="Filter by specialization"),
):
    """
    Get list of all teachers with pagination and optional filters.
    """
    query: Select = select(Student)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Student.first_name).like(search_term),
                func.lower(Student.last_name).like(search_term),
                func.lower(Student.email).like(search_term),
            )
        )
   
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * limit
    query = query.order_by(Student.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    teachers = result.scalars().all()


    return teachers



@router.get("/check-exists/{email}", response_model=bool)
async def check_student_exists(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Check if a student profile exists by email"""
    result = await db.execute(
        select(Student).where(func.lower(Student.email) == email.lower())
    )
    student = result.scalar_one_or_none()
    return student is not None
