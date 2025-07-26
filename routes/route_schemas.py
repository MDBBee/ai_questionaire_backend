from typing import List, Optional
from pydantic import BaseModel, Field
from ..agents.agent_schemas import QuestionModel
import uuid


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


