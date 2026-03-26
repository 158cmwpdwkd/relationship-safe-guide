from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Order, PremiumReport, Report, UserSession
from app.routes_report import resolve_free_report_html, resolve_premium_report_html
from app.services.interpretation.schemas import PaidSurveyAnswers
from app.services import premium_report as premium_service


def build_answers(seed: str = "base") -> PaidSurveyAnswers:
    return PaidSurveyAnswers(
        q1=f"{seed}-q1",
        q2=f"{seed}-q2",
        q3=f"{seed}-q3",
        q4=f"{seed}-q4",
        q5=f"{seed}-q5",
        q6=f"{seed}-q6",
        q7=f"{seed}-q7",
        q8=f"{seed}-q8",
        q9=f"{seed}-q9",
        q10=f"{seed}-q10",
        q11=f"{seed}-q11",
        q12=f"{seed}-q12",
        q13=f"{seed}-q13",
        q14=f"{seed}-q14",
        q15=f"{seed}-q15",
        q16=f"{seed}-q16",
        q17=f"{seed}-q17",
        q18=[f"{seed}-q18"],
        q19=[f"{seed}-q19"],
        q20=f"{seed}-q20",
    )


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db, TestingSessionLocal
    finally:
        db.close()


def create_free_session_and_order(db, *, sid: str, free_token: str, order_id: str, status: str = "PAID"):
    session = UserSession(
        sid=sid,
        risk_level="LOW",
        impulse_index=2,
        fear_type="fear_end_forever",
        free_answers_json="{}",
        red_flags_json="[]",
    )
    db.add(session)
    db.add(
        Report(
            sid=sid,
            status="READY",
            report_token=free_token,
            markdown="",
            html="",
        )
    )
    db.add(
        Order(
            order_id=order_id,
            sid=sid,
            free_report_token=free_token,
            status=status,
            amount=29000,
        )
    )
    db.commit()


def stub_generation(monkeypatch):
    monkeypatch.setattr(
        premium_service,
        "generate_premium_report_artifacts",
        lambda prompt, metrics: {
            "markdown": f"# premium {prompt}",
            "html": f"<html><body>{prompt}</body></html>",
        },
    )


def test_normal_flow_creates_order_bound_survey_and_premium_report(db_session, monkeypatch):
    db, _ = db_session
    create_free_session_and_order(db, sid="S1", free_token="t_free_1", order_id="O1")
    stub_generation(monkeypatch)

    saved = premium_service.submit_paid_survey(
        order_id="O1",
        answers=build_answers("one"),
        submitted_at=None,
        db=db,
    )
    premium_report, state, _, reused_existing = premium_service.run_premium_pipeline(
        order_id="O1",
        db=db,
        overwrite=False,
    )

    assert saved.order_id == "O1"
    assert state.state == "READY"
    assert reused_existing is False
    assert premium_report.order_id == "O1"
    assert premium_report.premium_report_token.startswith("t_premium_")
    assert db.query(PremiumReport).filter(PremiumReport.order_id == "O1").count() == 1


def test_same_sid_multiple_orders_do_not_share_paid_survey_or_premium_report(db_session, monkeypatch):
    db, _ = db_session
    create_free_session_and_order(db, sid="S1", free_token="t_free_same", order_id="O1")
    db.add(
        Order(
            order_id="O2",
            sid="S1",
            free_report_token="t_free_same",
            status="PAID",
            amount=29000,
        )
    )
    db.commit()
    stub_generation(monkeypatch)

    premium_service.submit_paid_survey(order_id="O1", answers=build_answers("one"), submitted_at=None, db=db)
    premium_service.submit_paid_survey(order_id="O2", answers=build_answers("two"), submitted_at=None, db=db)
    report1, _, _, _ = premium_service.run_premium_pipeline(order_id="O1", db=db, overwrite=False)
    report2, _, _, _ = premium_service.run_premium_pipeline(order_id="O2", db=db, overwrite=False)

    assert report1.order_id == "O1"
    assert report2.order_id == "O2"
    assert report1.premium_report_token != report2.premium_report_token
    assert db.query(PremiumReport).count() == 2


def test_generate_is_idempotent_per_order(db_session, monkeypatch):
    db, _ = db_session
    create_free_session_and_order(db, sid="S1", free_token="t_free_1", order_id="O1")
    stub_generation(monkeypatch)
    premium_service.submit_paid_survey(order_id="O1", answers=build_answers("one"), submitted_at=None, db=db)

    report1, _, _, reused1 = premium_service.run_premium_pipeline(order_id="O1", db=db, overwrite=False)
    report2, _, _, reused2 = premium_service.run_premium_pipeline(order_id="O1", db=db, overwrite=False)

    assert reused1 is False
    assert reused2 is True
    assert report1.premium_report_token == report2.premium_report_token
    assert db.query(PremiumReport).filter(PremiumReport.order_id == "O1").count() == 1


def test_free_token_cannot_open_premium_report_route(db_session, monkeypatch):
    db, SessionLocal = db_session
    create_free_session_and_order(db, sid="S1", free_token="t_free_1", order_id="O1")
    stub_generation(monkeypatch)
    premium_service.submit_paid_survey(order_id="O1", answers=build_answers("one"), submitted_at=None, db=db)
    premium_report, _, _, _ = premium_service.run_premium_pipeline(order_id="O1", db=db, overwrite=False)

    monkeypatch.setattr("app.routes_report.SessionLocal", SessionLocal)

    free_html = resolve_free_report_html("t_free_1")
    premium_html = resolve_premium_report_html(premium_report.premium_report_token)

    assert free_html.status_code == 200
    assert premium_html.status_code == 200
    with pytest.raises(HTTPException) as exc:
        resolve_premium_report_html("t_free_1")
    assert exc.value.status_code == 404


def test_frontend_uses_refactored_endpoint_and_keys():
    premium_survey_html = Path("imweb/imweb premium-survey.html").read_text(encoding="utf-8")
    premium_wrapper_html = Path("imweb/premium_report.html").read_text(encoding="utf-8")
    free_report_html = Path("imweb/imweb free-report.html").read_text(encoding="utf-8")

    assert "/api/premium/survey/submit" in premium_survey_html
    assert "/api/survey/paid" not in premium_survey_html
    assert "rl_active_order_id" in premium_survey_html
    assert 'orderId' in premium_wrapper_html
    assert 'rl_active_order_id' in premium_wrapper_html
    assert '/report?token=' in free_report_html
