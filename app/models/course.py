"""Course model"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin


class CourseStatus(str, enum.Enum):
    """Course status enum"""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Course(Base, TimestampMixin):
    """Course model"""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., MATH101
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    max_students = Column(Integer, default=30, nullable=False)
    duration_weeks = Column(Integer, nullable=False)  # Course duration in weeks
    status = Column(
        SQLEnum(CourseStatus),
        default=CourseStatus.DRAFT,
        nullable=False,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    teacher = relationship("Teacher", back_populates="courses")
    category = relationship("Category")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course(id={self.id}, code='{self.code}', title='{self.title}')>"

    @property
    def enrolled_count(self):
        """Get count of enrolled students"""
        return len([e for e in self.enrollments if e.is_active])

    @property
    def is_full(self):
        """Check if course is at capacity"""
        return self.enrolled_count >= self.max_students
