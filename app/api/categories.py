"""Category endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.models.category import Category
from app.middleware.auth import get_current_user, CurrentUser, UserRole
from app.cache import cache, get_cache_key

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new category (Admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create categories",
        )

    # Check if name or slug already exists
    result = await db.execute(
        select(Category).where(
            (Category.name == category_data.name) | (Category.slug == category_data.slug)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name or slug already exists",
        )

    category = Category(**category_data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)

    # Invalidate cache
    await cache.delete_pattern("categories:*")

    return category


@router.get("/", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all categories"""
    # Try to get from cache
    cache_key = get_cache_key("categories", "list")
    cached_data = await cache.get(cache_key)
    if cached_data:
        return cached_data

    result = await db.execute(select(Category))
    categories = result.scalars().all()

    # Convert to list of dicts for caching
    categories_data = [
        {
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "slug": cat.slug,
            "created_at": cat.created_at.isoformat(),
            "updated_at": cat.updated_at.isoformat(),
        }
        for cat in categories
    ]

    # Cache the result
    await cache.set(cache_key, categories_data)

    return categories_data


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific category by ID"""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    return category
