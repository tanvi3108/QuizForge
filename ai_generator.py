import warnings
warnings.filterwarnings("ignore")
import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_quiz(text, num_questions=15):
    prompt = f"""You are an expert quiz creator. Based on the following study material, generate exactly {num_questions} high quality multiple choice questions.

Rules:
- Questions must be directly based on the study material
- Each question must have exactly 4 options labeled A, B, C, D
- Questions should be tricky and test deep understanding
- Vary the difficulty: some easy, some medium, some hard
- Never repeat similar questions
- Return ONLY a valid JSON array, nothing else, no explanation, no markdown

Format:
[
  {{
    "question": "Question text here?",
    "options": ["A. option1", "B. option2", "C. option3", "D. option4"],
    "answer": "A. option1"
  }}
]

Study Material:
{text[:6000]}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4000
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'```json|```', '', raw).strip()
    questions = json.loads(raw)
    return questions


def generate_flashcards(text, num_cards=15):
    prompt = f"""You are an expert educator. Based on the following study material, generate exactly {num_cards} flashcards.

Rules:
- Each flashcard must have a clear concept or term on the front
- The back should have a concise easy to remember definition or explanation
- Focus on the most important keywords and concepts
- Keep definitions short — maximum 2 sentences
- Return ONLY a valid JSON array, nothing else, no explanation, no markdown

Format:
[
  {{
    "front": "Term or concept here",
    "back": "Clear and concise definition or explanation here"
  }}
]

Study Material:
{text[:6000]}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4000
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r'```json|```', '', raw).strip()
    cards = json.loads(raw)
    return cards