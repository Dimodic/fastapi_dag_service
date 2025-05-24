import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@db:5432/graphdb"
)

Base = declarative_base()

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)