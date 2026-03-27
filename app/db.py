import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# ✅ 로컬 개발 fallback: DATABASE_URL이 없으면 sqlite 사용
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./dev.db"

def normalize_db_url(url: str) -> str:
    """
    Render Postgres는 보통 postgres:// 또는 postgresql:// 로 줌
    SQLAlchemy가 기본 psycopg2로 잡지 않게 psycopg3 드라이버를 강제.
    """
    if not url:
        return url

    # postgres://user:pass@host/db  -> postgresql+psycopg://user:pass@host/db
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]

    # postgresql://user:pass@host/db -> postgresql+psycopg://user:pass@host/db
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]

    # 이미 다른 드라이버 지정이면 그대로
    return url

DATABASE_URL = normalize_db_url(DATABASE_URL)
# ✅ sqlite일 때만 connect_args 필요
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# (중요) sqlite connect_args 같은거 여기 넣지 말기. Postgres는 불필요.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_runtime_schema() -> None:
    """
    Lightweight runtime schema sync for the dev/prototype deployment model.
    Creates new tables via metadata and adds missing `orders` columns that
    older environments will not get from `create_all`.
    """
    Base.metadata.create_all(bind=engine)

    order_columns = {
        "free_report_token": "VARCHAR(128)",
        "payment_method": "VARCHAR(32)",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
    }
    report_columns = {
        "free_kakao_sent_at": "TIMESTAMP",
    }
    premium_report_columns = {
        "premium_kakao_sent_at": "TIMESTAMP",
    }

    with engine.begin() as conn:
        inspector = inspect(conn)
        existing_tables = set(inspector.get_table_names())
        if "orders" in existing_tables:
            existing_columns = {col["name"] for col in inspector.get_columns("orders")}
            for column_name, column_type in order_columns.items():
                if column_name in existing_columns:
                    continue
                conn.execute(text(f"ALTER TABLE orders ADD COLUMN {column_name} {column_type}"))

        if "reports" in existing_tables:
            existing_columns = {col["name"] for col in inspector.get_columns("reports")}
            for column_name, column_type in report_columns.items():
                if column_name in existing_columns:
                    continue
                conn.execute(text(f"ALTER TABLE reports ADD COLUMN {column_name} {column_type}"))

        if "premium_reports" in existing_tables:
            existing_columns = {col["name"] for col in inspector.get_columns("premium_reports")}
            for column_name, column_type in premium_report_columns.items():
                if column_name in existing_columns:
                    continue
                conn.execute(text(f"ALTER TABLE premium_reports ADD COLUMN {column_name} {column_type}"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
