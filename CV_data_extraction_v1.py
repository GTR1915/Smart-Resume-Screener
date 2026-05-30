from openai import OpenAI
import os
from dotenv import load_dotenv
import pdfplumber
import json

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found. Create a .env file using .env.example.")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)
def pdf_to_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            page_text = p.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_resume_data(pdf_path):
    text = pdf_to_text(pdf_path)

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        max_tokens=1200,
        messages=[
            {
                "role": "system",
                "content": """
You are an AI Resume Parser. Convert ALL information into STRICT quantitative, normalized form.

RESPOND ONLY IN JSON with these rules:

1. name: string
2. email: string
3. phone: string

4. skills: list of objects:
   - Programming Language: list of programming languages
   - OS: List of operating system
   - Literature Language: list of literature language

5. experience: list of jobs:
   - title: string
   - company: string
   - start_year: number
   - start_month: number
   - end_year: number or null
   - end_month: number or null
   - responsibilities: list of strings
   - duration_months: number

6. education:
   - degree: string
   - institution: string
   - graduation_year: number
   - gpa: number or null

7. projects: list of:
   - title: string
   - start_year: number
   - start_month: number
   - end_year: number
   - end_month: number
   - technologies: list of strings

Rules:
- Convert all dates into numbers.
- Convert GPA into a number.
- Extract all technologies as skills.
- Add numeric fields even if guessed.
- If a value is unclear, set null.
"""
            },
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content


# Usage
if __name__ == "__main__":
    data = extract_resume_data("Resume\EPS-Computer-Science_Resume_Sample.pdf")
    print(data)
