"""ORM models for the `core` schema. Alembic migrations remain the source of truth."""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, MetaData, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    metadata = MetaData(schema="core")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    vm_ip: Mapped[str | None] = mapped_column(Text)
    archived: Mapped[bool] = mapped_column(server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(Text, unique=True)  # e.g. "week-0/first-peer"
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    steps: Mapped[int]
    archived: Mapped[bool] = mapped_column(server_default=text("false"))


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"))
    network_id: Mapped[str | None] = mapped_column(Text, unique=True)
    seed: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metrics: Mapped[dict | None] = mapped_column(JSONB)

    group: Mapped[Group] = relationship()
    challenge: Mapped[Challenge] = relationship()


class RunAssertion(Base):
    __tablename__ = "run_assertions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    step_index: Mapped[int]
    name: Mapped[str] = mapped_column(Text)
    params: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    passed: Mapped[bool]
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text)


class GroupAchievement(Base):
    __tablename__ = "group_achievements"

    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), primary_key=True)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"), primary_key=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GroupHealth(Base):
    __tablename__ = "group_health"

    __table_args__ = (Index("ix_group_health_group_ts", "group_id", "timestamp"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    state: Mapped[str] = mapped_column(Text)
    failures: Mapped[int] = mapped_column(server_default=text("0"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
