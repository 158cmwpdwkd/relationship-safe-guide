from sqlalchemy import String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .db import Base

def now():
    return datetime.utcnow()

class UserSession(Base):
    __tablename__ = "user_sessions"
    sid: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    # 무료 설문 (json을 텍스트로 저장: MVP 단순화)
    free_answers_json: Mapped[str] = mapped_column(Text, default="{}")
    impulse_index: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW")
    fear_type: Mapped[str] = mapped_column(String(30), default="")

    # 레드플래그 (json 텍스트)
    red_flags_json: Mapped[str] = mapped_column(Text, default="[]")

    # 연락처/동의
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    consent_collection_use: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_cross_border: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_version: Mapped[str] = mapped_column(String(30), default="v1")
    consent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    consent_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consent_ua: Mapped[str | None] = mapped_column(Text, nullable=True)

    order = relationship("Order", back_populates="session", uselist=False)
    paid = relationship("PaidSurvey", back_populates="session", uselist=False)
    report = relationship("Report", back_populates="session", uselist=False)

class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sid: Mapped[str] = mapped_column(String(64), ForeignKey("user_sessions.sid"))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING/PAID/FAILED/REFUND_REQUESTED/REFUNDED
    amount: Mapped[int] = mapped_column(Integer, default=9900)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pg_payload_json: Mapped[str] = mapped_column(Text, default="{}")

    session = relationship("UserSession", back_populates="order")

class PaidSurvey(Base):
    __tablename__ = "paid_surveys"
    sid: Mapped[str] = mapped_column(String(64), ForeignKey("user_sessions.sid"), primary_key=True)
    answers_json: Mapped[str] = mapped_column(Text, default="{}")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    session = relationship("UserSession", back_populates="paid")

class Report(Base):
    __tablename__ = "reports"
    sid: Mapped[str] = mapped_column(String(64), ForeignKey("user_sessions.sid"), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="GENERATING")  # BLOCKED/GENERATING/READY/FAILED
    markdown: Mapped[str] = mapped_column(Text, default="")
    html: Mapped[str] = mapped_column(Text, default="")
    report_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    session = relationship("UserSession", back_populates="report")

class MessageSchedule(Base):
    __tablename__ = "message_schedules"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sid: Mapped[str] = mapped_column(String(64), ForeignKey("user_sessions.sid"))
    type: Mapped[str] = mapped_column(String(20))  # REPORT_READY/CHECK_72H/CHECK_14D
    send_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING/SENT/FAILED
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)