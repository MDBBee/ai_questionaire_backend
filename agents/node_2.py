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

    if state["number_of_retries"] >= 4:
        return state
    
    title_of_existing_questions= state["existing_questions"]
    if len(state["existing_questions"]) == 0:
        return state

    system_prompt = f"""
        You are a validation agent responsible for ensuring the uniqueness and correctness of coding questions before final output. Below is a list of the generated coding questions and a list of the title of existing questions with which you are to validate against the recently generated coding questions. 

        CODING QUESTION: {state['generated_questions']}
        EXISTING QUESTIONS: {title_of_existing_questions} 

        You have two tasks labelled(Task-1 and Task-2), First task will be carried out now why the second will be carried out iteratively with other sub-tasks for the purpose of efficiency.

        Task-1: Analyze each provided question and compare them against a reference set of previously stored questions (considered as already used).

        For each new question:
        - Compare only the `title`  to existing questions title.
        - If the title is identical to any existing title, add the question to the "duplicate_question" field/attribute of the pydantic model provided for structured output.
        - The goal is to ensure a fresh experience for users and avoid repetition.

        Do not rewrite or modify the questions — simply assess and filter out duplicates.

        From the input respond with two lists of-(List-1 and List-2)

        List-1) unique_questions: **only the unique questions, add complete question, including the options and all other attributes of the question object from CODING QUESTION that are found to be unique. Task-2: Before appending each unique question, check if the value of the -correct_answer_id-(This is a property in the pydatic model) is actually the index of the correct answer, sometimes the -correct_answer_id- value references the wrong answer, if the -correct_answer_id- value references the wrong answer, you are to correct it by changing the value to reference the index of the correct answer**

        List-2) duplicate_questions: **duplicate question or questions, add only the duplicate questions from the  CODING QUESTIONs to this list. The duplicate quetion should be added in it's entirety!** .

        Note: If "EXISTING QUESTIONS" is an empty list, ignore the comparism, by returning all "CODING QUESTION" as new/unique.

        Task-2: From the unique_questions list
    """
    
    llm_unique = llm.with_structured_output(UniqueModel)

    response = llm_unique.invoke([SystemMessage(content=system_prompt), HumanMessage(content="check for duplicate questions, respond with the provided structure.")])
    
    if(len(response.duplicate_questions) > 0 ):
        # state["existing_questions"] = state["existing_questions"] + [q.title for q in response.duplicate_questions]
        state["existing_questions"] = [q.title for q in response.duplicate_questions]
    state["duplicate_questions"] = response.duplicate_questions
    state["accepted_questions"] =  response.unique_questions
    state["number_of_retries"] = state["number_of_retries"] + 1

    return state

def router(state: State):
    # print("😎😎🐳🐳ROT_DUP", len(state["duplicate_questions"]), state["duplicate_questions"])
    if state["number_of_retries"] >= 4:
        return "end"
    
    if len(state['duplicate_questions']) > 0 or len(state["accepted_questions"]) != 10:
        return "generate_questions"
  
    return "end"
  
