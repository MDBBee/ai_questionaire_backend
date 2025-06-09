import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI
from typing import Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.6)

class S_outPut(BaseModel):
    title: str = Field(description="Title of the question")
    options: list[str] = Field(min_length=4, description="Options to answer the question, should contain only one correct answer to the question, other options should be pausible")
    correct_answer_id: int = Field(description="Index of the correct answer/option, zero index base")
    explanation: str =Field(description="Detailed explanation of why the correct answer is right")

def generate_questions_with_ai(difficulty: str) -> S_outPut:      
    system_prompt = """You are an expert coding challenge creator. 
    Your task is to generate a coding question with multiple choice answers.
    The question should be appropriate for the specified difficulty level.

    For easy questions: Focus on basic syntax, simple operations, or common programming concepts.
    For medium questions: Cover intermediate concepts like data structures, algorithms, or language features.
    For hard questions: Include advanced topics, design patterns, optimization techniques, or complex algorithms.

    Return the challenge in the following JSON structure:
    {
        "title": "The question title",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_answer_id": 0, // Index of the correct answer (0-3)
        "explanation": "Detailed explanation of why the correct answer is right"
    }

    Make sure the options are plausible but with only one clearly correct answer.
    """

    llm_ws = llm.with_structured_output(S_outPut)

    try:
        response = llm_ws.astream_events( [{"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a {difficulty} difficulty coding challenge."}], )
        
       

        # required_fields = ["title", "options", "correct_answer_id", "explanation"]
        # for field in required_fields:
        #     if field not in challenge_data:
        #         raise ValueError(f"Missing required field: {field}")
        ans = {
            "title": response.title,
            "options": response.options,
             "correct_answer_id": response.correct_answer_id,
             "explanation": response.explanation
        }
        
      
        print("ans")
        return ans

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


# abs =  generate_questions_with_ai("medium")
# print("" == undefined)