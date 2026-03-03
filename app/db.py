import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

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

# (중요) sqlite connect_args 같은거 여기 넣지 말기. Postgres는 불필요.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()