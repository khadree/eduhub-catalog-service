"""Teacher endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

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

    # Check if user_id or email already exists
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
