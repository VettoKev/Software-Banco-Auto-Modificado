from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

import config

import sys

# -----------------------------------------------------------------------------
# Build the connection URL
# -----------------------------------------------------------------------------
DATABASE_URL = (
    f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    f"?charset=latin1"
)

# -----------------------------------------------------------------------------
# Engine
# -----------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_recycle=config.DB_POOL_RECYCLE,
    pool_pre_ping=config.DB_POOL_PRE_PING,
    echo=config.DEBUG,          # logs all SQL when DEBUG=True — turn off in production
)

# -----------------------------------------------------------------------------
# Session factory
# -----------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

def get_session():
    return SessionLocal()

def verify_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"Conectado a '{config.DB_NAME}' en {config.DB_HOST}:{config.DB_PORT}")
        return True
    except OperationalError as exc:
        print(f"FALLO al conectar a '{config.DB_NAME}': {exc}", file=sys.stderr)
        return False

if __name__=="__main__":
    verify_connection()