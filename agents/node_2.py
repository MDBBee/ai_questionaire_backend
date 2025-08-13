from typing import List

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from ..agents.agent_schemas import QuestionModel, State





load_dotenv()
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

class UniqueModel(BaseModel):
    unique_questions : List[str] = Field(description="A list of the title of questions selected as unique after comparing against existing questions")
    duplicate_questions : List[str] = Field(description="A list of questions/title selected as duplicate after comparing against existing questions")


def uniqueness_validator(state: State):
    print("STATE IN VALIDATOR")
    print("LEN-Gen--", len(state["generated_questions"]))
    print("LEN-Exis--", len(state["existing_questions"]))
    print("NO_Quest_TO_Gen--", state["number_of_questions_to_generate"])
    print("EXAMPLE--", state["generated_questions"][0])
   

    try:

        if state["number_of_retries"] >= 4:
            return state
            
        title_of_existing_questions = state["existing_questions"]

        # Generate titles from recent generation
        if len(title_of_existing_questions) == 0 and (len(state["generated_questions"])  >= state["number_of_questions_to_generate"]):

            state["accepted_questions"] = state["generated_questions"]
            state["number_of_questions_to_generate"] = 0


            return state
        
        if len(title_of_existing_questions) == 0 and (len(state["generated_questions"])  < state["number_of_questions_to_generate"]):

            state["accepted_questions"] = state["generated_questions"]

            state["number_of_questions_to_generate"] =  state["number_of_questions_to_generate"] - state["generated_questions"]

            state["existing_questions"] = [quest.title for quest in state["accepted_questions"]]
        
            return state
        
        # Half the title in order to avoid overflooding the model with query
        if len(title_of_existing_questions) >= 30 or (state["difficulty"] in ["medium", "hard"]):
            if(len(title_of_existing_questions) > 0 and state["difficulty"] in ["medium", "hard"]):
                title_of_existing_questions = title_of_existing_questions[-10:]
            else:
                title_of_existing_questions = title_of_existing_questions[-30:]
        title_of_generated_questions = [gen_quest.title for gen_quest in state["generated_questions"]]


        system_prompt = f"""
            You are a validation agent responsible for ensuring the uniqueness of coding questions before final output. Below are two lists. First list contains the title of newly generated [CODING QUESTIONS] and the second list consists of the titles of existing questions [EXISTING QUESTIONS] with which you are to validate against. Compare each title from [CODING QUESTIONS] list with that of [EXISTING QUESTIONS] list.

            CODING QUESTIONS: {title_of_generated_questions}
            EXISTING QUESTIONS: {title_of_existing_questions} 

            You have only one main task(Task-1) and other sub-tasks. 

        [ Task-1]: Validate the uniqueness of the title of each newly generated question-[CODING QUESTIONS] by comparing them against a list of previously stored questions-[EXISTING QUESTIONS].

            Again for each new question [CODING QUESTIONS]:
            - Compare each title(item of the the list) to those of the existing questions[EXISTING QUESTIONS] list.
            - If the title is identical to any existing title in the [EXISTING QUESTIONS], add the question to the "duplicate_question" field/attribute of the pydantic model provided for structured output.
            - If the title is incomplete and doesn't make any sense, add the title to the "duplicate_question" field/attribute of the pydantic model provided for structured output.

            - The goal is to ensure a fresh experience for users and avoid repetition.

            Do not rewrite or modify the questions — simply assess and filter out duplicates and incomplete titles.

            From the pydantic model structured output, two lists are expected.

            List-1) unique_questions: **only the unique/validated questions, add the complete question title from [CODING QUESTIONS] list which are found to be unique. 

            List-2) duplicate_questions: **duplicate question or questions, add only the duplicate and incomplete titles from the  [CODING QUESTIONs] to this list. 

            Note: If "EXISTING QUESTIONS" is an empty list, ignore the comparism, by returning all "CODING QUESTION" as new/unique.
        """

        llm_unique = llm.with_structured_output(UniqueModel)

        response = llm_unique.invoke([SystemMessage(content=system_prompt), HumanMessage(content="check for duplicate questions, respond with the provided structure.")])


        unique_questions = []
        if response.unique_questions:
            for dup_quest in state["generated_questions"]:
                if dup_quest.title in response.unique_questions:
                    unique_questions.append(dup_quest)

        duplicate_questions = []
        if response.duplicate_questions:
            for dup_quest in state["generated_questions"]:
                if dup_quest.title in response.duplicate_questions:
                    duplicate_questions.append(dup_quest)

        state["duplicate_questions"] = duplicate_questions
        state["accepted_questions"] =  unique_questions

        state["number_of_questions_to_generate"] =  state["number_of_questions_to_generate"] - len(unique_questions)

        state["number_of_retries"] = state["number_of_retries"] + 1

        return state

    except Exception as e:
        print(str(e))
    

def router(state: State):
  
    if state["number_of_retries"] >= 4:
        return "end"
    
    if state["number_of_questions_to_generate"] > 0 and len(state["accepted_questions"]) < 10:
        return "generate_questions"
  
    return "end"
  