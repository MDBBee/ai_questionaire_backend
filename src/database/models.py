from sqlalchemy import Boolean, Column, Integer, String, DateTime, create_engine, ForeignKey
from fastapi import Depends
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime, timezone
from typing import Annotated

engine = create_engine('sqlite:///dbase.db', echo=True)
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
    role = Column(String)

    challenges = relationship("Challenge", back_populates="user", cascade="all, delete-orphan")
    challenge_quotas = relationship("ChallengeQuota", back_populates="user", cascade="all, delete-orphan")
     

class Challenge(Base):
    __tablename__ = 'challenges'

    id = Column(Integer, primary_key=True)
    difficulty = Column(String, nullable=False)
    programming_language = Column(String, nullable=False)
    date_created = Column(DateTime, default=datetime.now(timezone.utc))
    created_by = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    options = Column(String, nullable=False)
    correct_answer_id = Column(Integer, nullable=False)
    user_answer = Column(Integer, nullable=True)
    explanation = Column(String, nullable=False)
    question_id = Column(String, unique=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="challenges")


class ChallengeQuota(Base):
    __tablename__ = 'challenge_quotas'

    id = Column(Integer, primary_key=True)
    quota_remaining = Column(Integer, nullable=False, default=50)
    last_reset_date = Column(DateTime, default=datetime.now(timezone.utc))

    user_id = Column(Integer, ForeignKey("users.id"))
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
# date_created = Column(DateTime, default=datetime.now(timezone.utc))  # ❌
# This sets the default once at startup, not per row insert. It will give every row the same timestamp, which is a subtle bug.
# default=lambda: datetime.now(timezone.utc)