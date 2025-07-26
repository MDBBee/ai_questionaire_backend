from langchain_core.messages import  HumanMessage
from langgraph.graph import  StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from ..agents.agent_schemas import State
from ..agents.node_1 import generate_questions_with_ai
from ..agents.node_2 import router, uniqueness_validator
from ..database.models import Challenge
from ..routes.route_schemas import ChallengeRequest



load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

builder = StateGraph(State)

builder.add_node("question_generator",generate_questions_with_ai)
builder.add_node("uniqueness_validator",uniqueness_validator)
# builder.add_node("final_validator",final_validator)


builder.set_entry_point("question_generator")
builder.add_edge("question_generator","uniqueness_validator")
builder.add_conditional_edges("uniqueness_validator",router, {"generate_questions":"question_generator", "end":END})

graph = builder.compile()

def generate_questions(questionSetting: ChallengeRequest, db: Session):

    programmingLanguage = questionSetting.programmingLanguage
    difficulty = questionSetting.difficulty
    existing_question_titles = [q.title for q in db.query(Challenge).filter(Challenge.difficulty == questionSetting.difficulty, Challenge.programming_language == questionSetting.programmingLanguage)]

    print("🐳🐳🐳🐳:::LOQ",len(existing_question_titles))

    human_message=f"Please Generate 10(ten) coding challenges/questions in {programmingLanguage} programming language. The difficulty level should be {difficulty}"
    
    entry_config = {
        "messages": [HumanMessage(content=human_message)],
        "difficulty": difficulty,
        "programmingLanguage": programmingLanguage,
        "duplicate_questions": [],
        "existing_questions": existing_question_titles,
        "accepted_questions": []
        }

    try:
        response = graph.invoke(input=entry_config)

        questions = []
        for t in response["accepted_questions"]:
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





