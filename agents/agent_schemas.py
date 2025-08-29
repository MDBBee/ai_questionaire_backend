from pydantic import BaseModel, Field, conlist
from typing import TypedDict, Annotated, List
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph import add_messages, StateGraph, END

class QuestionModel(BaseModel):
    title: str = Field(description="The question itself.**COMPLETENESS IS THE ABSOLUTE PRIORITY.** Do not generate incomplete questions. **If a question refers to a code snippet, that *full and complete* code snippet MUST be included directly within this field ('title' field).** For example, 'What's the final output of this JavaScript code snippet?' is incomplete without the actual snippet. This is not the topic, this field should hold the question which is to be addressed by the options field")
    options: list[str] = Field(min_length=4, description="Options to answer the question, should contain only ONE CORRECT ANSWER to the question, other options should be close to the correct answer. There should only be ONE CORRECT answer to the question")
    correct_answer_id: int = Field(description="Index of the correct answer/option, zero index base")
    explanation: str =Field(description="Detailed explanation of the reason behind the answer")

class QuestionOutput(BaseModel):
    questions: conlist(QuestionModel,min_length=5, max_length=12) = Field(description="List of coding questions")
    
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    programmingLanguage: Annotated[str, "accumulate"]  
    difficulty: Annotated[str, "accumulate"]  
    generated_questions: List[QuestionModel]
    existing_questions: List[str]
    accepted_questions: List[QuestionModel]
    duplicate_questions: List[QuestionModel]
    number_of_retries: int
    number_of_questions_to_generate: int
    error: str