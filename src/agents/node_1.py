from langchain_core.messages import SystemMessage
from ..agents.agent_schemas import QuestionOutput, State
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os


load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

def generate_questions_with_ai(state: State) -> State:
    NO_QUESTIONS_TO_GENERATE = 10

        
    if len(state["duplicate_questions"]) >0:
        NO_QUESTIONS_TO_GENERATE = len(state["duplicate_questions"])

        
    system_prompt = f"""
        You are an expert coding challenge creator for Python, TypeScript, and JavaScript. 
        Your task is to generate {NO_QUESTIONS_TO_GENERATE} high-quality coding questions, each with 4 multiple-choice answers and exactly one correct answer.

        Each question must match the following constraints:
        - Programming Language: {state['programmingLanguage']}
        - Difficulty Level: {state['difficulty']}

        ### Difficulty Guidelines:
        - **Easy**: Basic syntax, variables, simple loops, conditional logic, string manipulation.
        - **Medium**: Functions, data structures (lists, dictionaries), iteration patterns, basic algorithms.
        - **Hard**: Recursion, time/space optimization, complex logic, advanced language features, object-oriented patterns.

        ### Requirements:
        1. Each generated question should have a different title, avoid using the same starting phrase (e.g, what is the output of the code....). The questions/title shouldn't be boring, apply wit and logic to each generated question.
        2. Avoid redundant or overly similar questions (e.g., don’t create multiple questions about the output of a code, `len()` or simple print statements). Ensure to touch different topics and apply different logic in the generated question, regardless of the difficulty. 
        3. Ensure conceptual diversity:
        - Cover a variety of topics like booleans, arithmetic, string ops, indexing, control flow, functions, error handling, and common algorithms.
        4. Keep the question titles clear, concise, and semantically distinct from one another.
        5. Do NOT reuse existing question titles. These must be unique:
        Existing question titles: {state["existing_questions"]}
        6. Ensure that the question title is complete and logical. Do not generate, incomplete questions

        ### Output Format:
        For each question, return:
        - `title`: The question to display. This shpould be the question to display not the name of the topic but the question itself
        - `options`: A list of 4 plausible answers (only ONE correct).
        - `correct_answer_id`: Index (0-based) of the correct option.
        - `explanation`: A clear, accurate explanation justifying the correct answer.

        NOTE: the "title" key/attribute is where the full question should be placed. Include all question code blocks.
        Please ensure random placement of the correct answer among the options.
        Do NOT generate, INCOMPLETE questions

        """


    llm_ws = llm.with_structured_output(QuestionOutput)

    response = llm_ws.invoke([SystemMessage(content=system_prompt) ] + state["messages"])
    
    state["generated_questions"] = response.questions

    return state

