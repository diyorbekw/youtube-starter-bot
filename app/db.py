# app/db.py
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DB_URL

engine = create_engine(
    DB_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,    
    pool_recycle=1800,       
    pool_size=5,
    max_overflow=10,
    connect_args={
        "connect_timeout": 5,
    }
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

Base = declarative_base()


def init_db():
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        Base.metadata.create_all(bind=engine)
