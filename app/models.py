from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now() -> datetime:
    return datetime.utcnow()


class UserSession(Base):
    __tablename__ = "user_sessions"

    sid: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    free_answers_json: Mapped[str] = mapped_column(Text, default="{}")
    impulse_index: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW")
    fear_type: Mapped[str] = mapped_column(String(30), default="")
    red_flags_json: Mapped[str] = mapped_column(Text, default="[]")

    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    consent_collection_use: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_cross_border: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_version: Mapped[str] = mapped_column(String(30), default="v1")
    consent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    consent_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consent_ua: Mapped[str | None] = mapped_column(Text, nullable=True)

    orders = relationship("Order", back_populates="session")
    free_report = relationship("Report", back_populates="session", uselist=False)
    paid_surveys = relationship("PaidSurvey", back_populates="session")
    premium_reports = relationship("PremiumReport", back_populates="session")


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sid: Mapped[str] = mapped_column(String(64), ForeignKey("user_sessions.sid"), index=True)
    free_report_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
    )  # PENDING/PAID/FAILED/VBANK_ISSUED/REFUND_REQUESTED/REFUNDED
    payment_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, default=9900)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pg_payload_json: Mapped[str] = mapped_column(Text, default="{}")

    session = relationship("UserSession", back_populates="orders")
    paid_survey = relationship("PaidSurvey", back_populates="order", uselist=False)
    premium_report = relationship("PremiumReport", back_populates="order", uselist=False)


class PaidSurvey(Base):
    __tablename__ = "paid_surveys_v2"

    order_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("orders.order_id"),
        primary_key=True,
    )
    sid: Mapped[str] = mapped_column(String(64), ForeignKey("user_sessions.sid"), index=True)
    answers_json: Mapped[str] = mapped_column(Text, default="{}")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    order = relationship("Order", back_populates="paid_survey")
    session = relationship("UserSession", back_populates="paid_surveys")


class Report(Base):
    __tablename__ = "reports"

    sid: Mapped[str] = mapped_column(String(64), ForeignKey("user_sessions.sid"), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="GENERATING")
    markdown: Mapped[str] = mapped_column(Text, default="")
    html: Mapped[str] = mapped_column(Text, default="")
    report_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session = relationship("UserSession", back_populates="free_report")


class PremiumReport(Base):
    __tablename__ = "premium_reports"

    order_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("orders.order_id"),
        primary_key=True,
    )
    sid: Mapped[str] = mapped_column(String(64), ForeignKey("user_sessions.sid"), index=True)
    free_report_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    premium_report_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default="GENERATING",
    )  # GENERATING/READY/FAILED
    markdown: Mapped[str] = mapped_column(Text, default="")
    html: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    order = relationship("Order", back_populates="premium_report")
    session = relationship("UserSession", back_populates="premium_reports")


class MessageSchedule(Base):
    __tablename__ = "message_schedules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sid: Mapped[str] = mapped_column(String(64), ForeignKey("user_sessions.sid"))
    type: Mapped[str] = mapped_column(String(20))
    send_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
