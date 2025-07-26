import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI
from typing import Dict, Any, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.9)

class QuestionModel(BaseModel):
    title: str = Field(description="Title of the question")
    options: list[str] = Field(min_length=4, description="Options to answer the question, should contain only one correct answer to the question, other options should be pausible")
    correct_answer_id: int = Field(description="Index of the correct answer/option, zero index base")
    explanation: str =Field(description="Detailed explanation of why the correct answer is right")
class QuestionOutput(BaseModel):
    questions: List[QuestionModel] = Field(description="List of coding questions")

def generate_questions_with_ai(difficulty: str) -> Dict[str, any]:      
    system_prompt = """You are an expert coding challenge creator. 
    Your task is to generate 5 different coding questions with multiple choice answers.
    The questions should be appropriate for the specified difficulty level.

    For easy questions: Focus on basic syntax, simple operations, or common programming concepts.
    For medium questions: Cover intermediate concepts like data structures, algorithms, or language features.
    For hard questions: Include advanced topics, design patterns, optimization techniques, or complex algorithms.

    Return the challenge in the following JSON structure:
    [
        {
            "title": "The question title",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer_id": 0, // Index of the correct answer (0-3)
            "explanation": "Detailed explanation of why the correct answer is right"
        }
    ]

    Make sure the options for each question are plausible but with only one clearly correct answer, the answers should be place at random indexes, try as much as possible to randomise the correct answer index{correct_answer_id}.
    """

    llm_ws = llm.with_structured_output(QuestionOutput)

    try:
        response = llm_ws.invoke( [{"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a {difficulty} difficulty coding challenge."}])
        

       
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


abs =  generate_questions_with_ai("medium")
print(abs)


# print("" == undefined)