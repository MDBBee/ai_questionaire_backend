from typing import List

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from ..agents.agent_schemas import QuestionModel, State
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv





load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

class UniqueModel(BaseModel):
    unique_questions : List[QuestionModel] = Field(description="A list of questions selected as unique after comparing against existing questions")
    duplicate_questions : List[str] = Field(description="A list of questions selected as duplicate after comparing against existing questions")


def uniqueness_validator(state: State):

    if state["number_of_retries"] > 4:
        print("✅✅✅🔐🔐🗝️🗝️🐳🐳RETRIES REACHED", "MAX RETRIES REACHED")

        return state
    
    title_of_existing_questions= state["existing_questions"]

    system_prompt = f"""
        You are a validation agent responsible for ensuring the uniqueness of coding questions before they proceed to final review. Below is a list of the coding questions and a list of the title of the existing questions to validate against. 

        CODING QUESTION: {state['generated_questions']}
        EXISTING QUESTIONS: {title_of_existing_questions} 

        Your task is to analyze the provided questions and compare them against a reference set of previously stored questions (considered as already used).

        For each new question:
        - Compare only the `title`  to existing questions title.
        - If the title is identical to any existing title, add the question to the "duplicate_question" field/attribute of the pydantic model provided for structured output.
        - The goal is to ensure a fresh experience for users and avoid repetition.

        Do not rewrite or modify the questions — simply assess and filter out duplicates.

        From the input respond with two lists of 
        1) unique_questions: **only the unique questions, add complete question, including the options and all other attributes of the question object from CODING QUESTION that are found to be unique**
        2) duplicate_questions: **duplicate question or questions, extract only the question title from the  CODING QUESTIONs that are found to be duplicates** .

        Note: If "EXISTING QUESTIONS" is an empty list, ignore the comparism, by returning all "CODING QUESTION" as new/unique.
    """
    
    llm_unique = llm.with_structured_output(UniqueModel)

    response = llm_unique.invoke([SystemMessage(content=system_prompt), HumanMessage(content="check for duplicate questions, respond with the provided structure.")])
    
    if(len(response.duplicate_questions) > 0 ):
        state["existing_questions"] = state["existing_questions"] + [q.title for q in response.duplicate_questions]

    state["accepted_questions"] = state["accepted_questions"] + response.unique_questions

    state["number_of_retries"] = state["number_of_retries"] + 1

    return state

def router(state: State):
    
    if state["number_of_retries"] >= 4:
        print("✅✅✅🔐🔐🗝️🗝️🐳🐳RETRIES REACHED", "MAX RETRIES REACHED")
        return "end"
    if len(state['duplicate_questions']) > 0 or len(state["accepted_questions"]) != 10:
        return "generate_questions"
    return "end"
    # if len(state['duplicate_questions']) > 0 or len(state["accepted_questions"]) != 10:
    #     return "generate_questions"