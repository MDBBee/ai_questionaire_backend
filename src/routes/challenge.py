import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from ..ai_generator import QuestionModel, generate_questions_with_ai
from ..database.db import (
    get_challenge_quota,
    create_challenge_quota,
    reset_quota_if_needed,
    get_user_challenges
)
from .auth import  active_user_dependnecy
from ..database.models import db_dependency
from ..database.models import Challenge
from datetime import datetime
import uuid

router = APIRouter()


class ChallengeRequest(BaseModel):
    difficulty: str
    programmingLanguage: str

    class Config:
        json_schema_extra = {"example": {"difficulty": "easy",  "programmingLanguage": "python"}}
        
class SaveQuestionsToHistory(BaseModel):
    correct_answer_id: int
    createdBy: str
    difficulty: str
    explanation: str
    options: List[str]
    title: str
    programmingLanguage: str
    userAnswer: Optional[int]
    question_id: str

class QuestionToFrontEndModel(QuestionModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class QuestionsToFrontEndOutput(BaseModel):
    questions: List[QuestionToFrontEndModel]

@router.post("/generate-challenge")
async def generate_challenge(questSettings: ChallengeRequest, active_user: active_user_dependnecy, db: db_dependency ):
    
    if questSettings.difficulty is None:
        return
    try:
        user_id = active_user.id
        quota = get_challenge_quota(db, user_id)
        if not quota:
            quota = create_challenge_quota(db, user_id)

        quota = reset_quota_if_needed(db, quota)

        if quota.quota_remaining <= 0:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Insufficient Quota")
        
         

        challenge_data = generate_questions_with_ai(questSettings)
        
        generated_questions = []
        for q_data in challenge_data:
            parsed_question = QuestionToFrontEndModel(**q_data)  # Validates & converts
            generated_questions.append(parsed_question)
            quota.quota_remaining -= 1

        db.commit()
        return QuestionsToFrontEndOutput(questions=generated_questions)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my_history")
async def my_history(questSettings: Request, db: db_dependency):
    
    user_id = questSettings.get("user_id")

    challenges = get_user_challenges(db, user_id)
    return {"challenges": challenges}

@router.post("/save_to_history")
async def save_challenges_to_history(db: db_dependency, data_to_be_saved: list[SaveQuestionsToHistory], active_user: active_user_dependnecy):

    challenges_to_save = []
    for challenge in data_to_be_saved:
        new_challenge =Challenge(difficulty=challenge.difficulty, programming_language=challenge.programmingLanguage, created_by=active_user.email, title=challenge.title, options=json.dumps(challenge.options), correct_answer_id=challenge.correct_answer_id, user_answer=challenge.userAnswer, explanation=challenge.explanation, question_id=challenge.question_id)

        challenges_to_save.append(new_challenge)

    db.add_all(challenges_to_save)
    db.commit()
        

    return {"success": True, "message":"Question section successfully saved!"}



@router.get("/quota")
async def get_quota( user_details: active_user_dependnecy,  db: db_dependency):
    
    user_id = user_details.id
    quota = get_challenge_quota(db, user_id)
    if not quota:
        return {
            "user_id": user_id,
            "quota_remaining": 50,
            "last_reset_date": datetime.now()
        }

    quota = reset_quota_if_needed(db, quota)
    return quota
