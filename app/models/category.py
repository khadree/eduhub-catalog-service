"""Category model"""
from sqlalchemy import Column, Integer, String, Text
from app.models.base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    """Course category model"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"
