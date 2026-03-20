from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Use 'autopilot' schema to avoid conflicts with other apps on shared DB
@event.listens_for(engine, "connect")
def _set_search_path(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("SET search_path TO autopilot, public")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
