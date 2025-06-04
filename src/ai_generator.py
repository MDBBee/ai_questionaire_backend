import os
import json
from openai import OpenAI
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("open_router_api_key"),
)


def generate_questions_with_ai(difficulty: str) -> Dict[str, Any]:
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
    try:
        response = client.chat.completions.create(
            model="nvidia/llama-3.3-nemotron-super-49b-v1:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a {difficulty} difficulty coding challenge."}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        # print("One step to content")
        content = response.choices[0].message.content
        print("🔥🔥🔥START", content, "🔥🔥🔥END")
        cont1 = content.split("``")[1].replace("`", "```")
        print("🔥🔥🔥Act1",cont1)

        challenge_data = json.loads(f"'{cont1}'")
        print("---challenge_data---", challenge_data)

        required_fields = ["title", "options", "correct_answer_id", "explanation"]
        for field in required_fields:
            if field not in challenge_data:
                raise ValueError(f"Missing required field: {field}")

        return challenge_data

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

a = generate_questions_with_ai("medium")
print("🔥🔥🔥A", a)