from sqlalchemy import Boolean, Column, Enum as SqlEnum, Integer, String, DateTime, create_engine, ForeignKey
from fastapi import Depends
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime, timezone
from typing import Annotated
from dotenv import load_dotenv
import os
from enum import Enum

load_dotenv()
db_url = os.getenv("DATABASE_URL")

if db_url is None:
    print("No db url found")

    
engine = create_engine(db_url, echo=False)
Base = declarative_base()

    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    disabled = Column(Boolean, default=False)
    provider = Column(String,)
    image = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False )

    challenges = relationship("Challenge", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    challenge_quotas = relationship("ChallengeQuota", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
     

class Challenge(Base):
    __tablename__ = 'challenges'

    id = Column(Integer, primary_key=True)
    difficulty = Column(String, nullable=False)
    programming_language = Column(String, nullable=False)
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    title = Column(String, nullable=False)
    options = Column(String, nullable=False)
    correct_answer_id = Column(Integer, nullable=False)
    user_answer = Column(Integer, nullable=True)
    explanation = Column(String, nullable=False)
    question_id = Column(String, unique=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User", back_populates="challenges")


class ChallengeQuota(Base):
    __tablename__ = 'challenge_quotas'

    id = Column(Integer, primary_key=True)
    quota_remaining = Column(Integer, nullable=False, default=50)
    last_reset_date = Column(DateTime, default=datetime.now(timezone.utc))

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User", back_populates="challenge_quotas")


Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
