"""Student endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
