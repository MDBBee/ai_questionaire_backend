import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI
from typing import Dict, Any, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

class FrontEndRequest(BaseModel):
    difficulty: str
    programmingLanguage: str

    class Config:
        json_schema_extra = {"example": {"difficulty": "easy",  "programmingLanguage": "python"}}


class QuestionModel(BaseModel):
    title: str = Field(description="The question")
    options: list[str] = Field(min_length=4, description="Options to answer the question, should contain only one correct answer to the question, other options should be plausible,")
    correct_answer_id: int = Field(description="Index of the correct answer/option, zero index base")
    explanation: str =Field(description="Detailed explanation of why the correct answer is right")

class QuestionOutput(BaseModel):
    questions: List[QuestionModel] = Field(description="List of coding questions")

def generate_questions_with_ai(request: FrontEndRequest) -> Dict[str, any]:
    system_prompt = f"""You are an expert coding challenge creator for python, typsescript and javascript programming languages. 
    Your task is to generate 2 different coding questions with multiple choice answers.
    The questions should be appropriate for the specified difficulty level. Consider the programming language and Difficulty level stated below.

    Difficulty Level: {request.difficulty}
    Programming Language: {request.programmingLanguage}


    For Difficulty Level - "easy": Focus on basic syntax, simple operations, or common programming concepts.
    For Difficulty Level - "medium": Cover intermediate concepts like data structures, algorithms, or language features.
    For Difficulty Level - "hard": Include advanced topics, design patterns, optimization techniques, or complex algorithms.


    Make sure the options for each question are plausible but with only one clearly correct answer, the answers should be placed at random indexes, try as much as possible to randomise the correct answer index and ensure that other options are plausible.
    """

    llm_ws = llm.with_structured_output(QuestionOutput)

    try:
        response = llm_ws.invoke( [{"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a {request.difficulty} difficulty coding challenge in {request.programmingLanguage}. programming language"}])
        

        questions = []
        for t in response.questions:
            question = {
                "title": t.title,
                "options": t.options,
                "correct_answer_id": t.correct_answer_id,
                "explanation": t.explanation
            }
            questions.append(question)
        
       
        return questions
       

    except Exception as e:
        print(e)
        return {
            "title": "Basic Python List Operation",
            "options": [
                "my_list.append(5)",
                "my_list.add(5)",
                "my_list.push(5)",
                "my_list.insert(5)",
            ],
            "correct_answer_id": 0,
            "explanation": "In Python, append() is the correct method to add an element to the end of a list."
        }

# generate_questions_with_ai("medium")