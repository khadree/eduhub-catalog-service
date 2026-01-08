from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.sql import Select
from typing import List

from app.database import get_db
from app.schemas.admin import AdminCreate, AdminUpdate, AdminResponse
from app.models.admin import Admin
from app.middleware.auth import get_current_user, CurrentUser, UserRole

router = APIRouter(prefix="/admins", tags=["Admins"])

@router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_data: AdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new admin (Admin only - possibly superadmin?)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create admin profiles",
        )

    result = await db.execute(
        select(Admin).where(
            (Admin.user_id == admin_data.user_id)
            | (Admin.email == admin_data.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this user_id or email already exists",
        )

    admin = Admin(**admin_data.model_dump())
    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    return admin


@router.get("/{admin_id}", response_model=AdminResponse)
async def get_admin(admin_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific admin by ID"""
    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found"
        )

    return admin


@router.get("/", response_model=List[AdminResponse])
async def get_admins(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search in name or email"),
    specialization: str | None = Query(None, description="Filter by specialization"),
):
    """
    Get list of all admins with pagination and optional filters.
    """
    query: Select = select(Admin)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Admin.first_name).like(search_term),
                func.lower(Admin.last_name).like(search_term),
                func.lower(Admin.email).like(search_term),
            )
        )
    if specialization:
        query = query.where(
            Admin.specialization.ilike(f"%{specialization}%")
        )

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * limit
    query = query.order_by(Admin.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    admins = result.scalars().all()

    return admins


@router.get("/check-exists/{email}", response_model=bool)
async def check_admin_exists(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Check if an admin profile exists by email"""
    result = await db.execute(
        select(Admin).where(func.lower(Admin.email) == email.lower())
    )
    admin = result.scalar_one_or_none()
    return admin is not None