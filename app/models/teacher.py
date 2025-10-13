"""Teacher model"""
from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Teacher(Base, TimestampMixin):
    """Teacher model"""

    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)  # Reference to auth service
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    bio = Column(Text, nullable=True)
    specialization = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    courses = relationship("Course", back_populates="teacher")

    def __repr__(self):
        return f"<Teacher(id={self.id}, name='{self.first_name} {self.last_name}')>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
