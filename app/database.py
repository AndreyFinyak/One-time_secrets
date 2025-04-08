import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    try:
        print("Database connection initialized")
    except Exception as e:
        print(f"Error initializing the database: {str(e)}")
        raise

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
