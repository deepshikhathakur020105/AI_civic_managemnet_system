import os

from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://civic:civic@localhost:5432/civic")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
