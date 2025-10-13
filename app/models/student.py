"""Student model"""
from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Student(Base, TimestampMixin):
    """Student model"""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)  # Reference to auth service
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    student_number = Column(String(50), unique=True, nullable=False, index=True)
    grade_level = Column(Integer, nullable=False)  # 7-12 for secondary school
    date_of_birth = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student(id={self.id}, student_number='{self.student_number}', name='{self.first_name} {self.last_name}')>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
