"""Enrollment model"""
from sqlalchemy import Column, Integer, ForeignKey, Boolean, Date, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import Base, TimestampMixin


class EnrollmentStatus(str, enum.Enum):
    """Enrollment status enum"""

    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    WITHDRAWN = "withdrawn"


class Enrollment(Base, TimestampMixin):
    """Enrollment model - links students to courses"""

    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    enrollment_date = Column(Date, nullable=False)
    status = Column(
        SQLEnum(EnrollmentStatus),
        default=EnrollmentStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

    # Constraints
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="unique_student_course"),
    )

    def __repr__(self):
        return f"<Enrollment(id={self.id}, student_id={self.student_id}, course_id={self.course_id}, status='{self.status}')>"
