"""Training workout-day and exercise-log models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WorkoutDay(Base):
    __tablename__ = "workout_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    week_number: Mapped[int] = mapped_column(Integer, default=1)
    day_type: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(16), default="not_started")
    skip_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    logs: Mapped[list["ExerciseLog"]] = relationship(
        back_populates="workout_day",
        cascade="all, delete-orphan",
        order_by="ExerciseLog.id",
    )


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"
    __table_args__ = (UniqueConstraint("workout_day_id", "exercise_key", name="uq_day_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_day_id: Mapped[int] = mapped_column(
        ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False, index=True
    )

    exercise_key: Mapped[str] = mapped_column(String(64), nullable=False)
    planned_name: Mapped[str] = mapped_column(String(128), default="")
    planned_sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    planned_reps: Mapped[str | None] = mapped_column(String(64), nullable=True)
    planned_duration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    planned_distance: Mapped[str | None] = mapped_column(String(64), nullable=True)

    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    actual_sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_reps: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    actual_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    rpe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    workout_day: Mapped["WorkoutDay"] = relationship(back_populates="logs")
