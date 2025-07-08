from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..ai_generator import generate_questions_with_ai
from ..database.db import (
    get_challenge_quota,
    create_challenge,
    create_challenge_quota,
    reset_quota_if_needed,
    get_user_challenges
)
from ..utils import authenticate_and_get_user_details
from ..database.models import get_db
import json
from datetime import datetime

router = APIRouter()


class ChallengeRequest(BaseModel):
    difficulty: str
    programmingLanguage: str

    class Config:
        json_schema_extra = {"example": {"difficulty": "easy",  "programmingLanguage": "python"}}


@router.post("/generate-challenge")
async def generate_challenge(request: ChallengeRequest, request_obj: Request, db: Session = Depends(get_db)):
    print("REQUEST FROM GC✅",request)
    if request.difficulty is None:
        return
    try:
        user_details = authenticate_and_get_user_details(request_obj)
        user_id = user_details.get("user_id")

        quota = get_challenge_quota(db, user_id)
        if not quota:
            quota = create_challenge_quota(db, user_id)

        quota = reset_quota_if_needed(db, quota)

        if quota.quota_remaining <= 0:
            raise HTTPException(status_code=429, detail="Insufficient Quota")
        
         

        challenge_data = generate_questions_with_ai(request)
        
        
        generated_questions = []
        for question in challenge_data:
            # Creating a question instance for db storage
            new_challenge = create_challenge(
                db=db,
                difficulty=request.difficulty,
                created_by=user_id,
                title=question["title"],
                options=json.dumps(question["options"]),
                correct_answer_id=question["correct_answer_id"],
                explanation=question["explanation"]
            )
            db.commit()
            quota.quota_remaining -= 1
            # Creating a question object for F_end
            front_end_question = {
                "id": new_challenge.id,
                "difficulty": request.difficulty,
                "title": new_challenge.title,
                "options": json.loads(new_challenge.options),
                "correct_answer_id": new_challenge.correct_answer_id,
                "explanation": new_challenge.explanation,
                "timestamp": new_challenge.date_created.isoformat()
            }
            generated_questions.append(front_end_question)
        return generated_questions

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-history")
async def my_history(request: Request, db: Session = Depends(get_db)):
    user_details = authenticate_and_get_user_details(request)
    user_id = user_details.get("user_id")

    challenges = get_user_challenges(db, user_id)
    return {"challenges": challenges}





@router.get("/quota")
async def get_quota(request: Request, db: Session = Depends(get_db)):
    user_details = authenticate_and_get_user_details(request)
    user_id = user_details.get("user_id")

    quota = get_challenge_quota(db, user_id)
    if not quota:
        return {
            "user_id": user_id,
            "quota_remaining": 50,
            "last_reset_date": datetime.now()
        }

    quota = reset_quota_if_needed(db, quota)
    return quota
