'''
This module is just an extention of CV_data_extraction_v1.py, it includes extra features such as save
the extracted data directly into local_database.db and for ease in debuging it includes saving the
extracted data in the pickle file so the debug the response it the data fails to get saved in the 
local_database.db
'''
from openai import OpenAI
from dotenv import load_dotenv
from typing import Any, Dict
import pdfplumber
import os
import json
import sqlite3
import pickle


load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
DB_PATH = os.getenv("DB_PATH")

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
        max_tokens=3000,
        messages=[
            {
"role": "system",
"content": """
You are an AI Resume Parser. Convert ALL information into STRICT quantitative, normalized form.

RESPOND ONLY IN JSON with these fields:

1. name: string
2. email: string
3. phone: string

4. skills: list of objects:
   - name: string
   - category: string (programming-language, framework, library, tool, cloud, database, os, soft-skill, language, other)

5. applied_skills: list of objects (skills actually used in experience/projects):
   - name: string
   - category: string

6. experience: list of jobs:
   - title: string
   - company: string
   - start_year: number
   - start_month: number
   - end_year: number or null
   - end_month: number or null
   - responsibilities: list of strings
   - duration_months: number

7. education: list of:
   - degree: string
   - institution: string
   - graduation_year: number or null
   - gpa: number or null

8. projects: list of:
   - title: string
   - start_year: number
   - start_month: number
   - end_year: number
   - end_month: number
   - technologies: list of strings

9. additional_info: list of extra items such as:
   - awards
   - certifications
   - publications
   - volunteering
   - achievements
   - extra courses
   - organizations
   - hobbies
   - other relevant sections

Rules:
- Convert all dates into numbers.
- Convert GPA into a number.
- Extract ALL technologies into skills.
- Extract ALL skills mentioned in projects/experiences into applied_skills.
- applied_skills MUST be a subset of skills.
- Preserve ALL information (put extra sections into "additional_info").
- If a value is unclear, set null.
"""
},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content

def str2json(s: str) -> Dict[str, Any]:
    """
    Parse a string that may contain a JSON code block (e.g. ```json\n{...}\n```)
    and return a Python dict.
    Args:
        s (str): Input string potentially containing JSON.
    Returns:
        Dict[str, Any]: Parsed JSON as a Python dictionary.
    Raises:
        ValueError: If no valid JSON could be parsed.
    """
    if not isinstance(s, str):
        raise ValueError("Input must be a string")
    
    try:
        return json.loads(s[8:-3])
    except json.JSONDecodeError as e:
        preview = s[:50] + "..." if len(s) > 50 else s
        raise ValueError(f"Failed to decode JSON. Error: {e}. Preview: {preview}") from e

def create_query(text):
    
    return ""

class ResumeDB:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")  # enable FKs in SQLite
        self.cursor = self.conn.cursor()

    def create_tables(self):
        # 1) main candidates table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT
            );
        """)

        # 2) skills table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
            );
        """)

        # 3) experience table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS experience (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                title TEXT,
                company TEXT,
                start_year INTEGER,
                start_month INTEGER,
                end_year INTEGER,
                end_month INTEGER,
                duration_months INTEGER,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
            );
        """)

        # 4) projects table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                title TEXT,
                start_year INTEGER,
                start_month INTEGER,
                end_year INTEGER,
                end_month INTEGER,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
            );
        """)

        # 5) education table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS education (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                degree TEXT,
                institution TEXT,
                graduation_year INTEGER,
                gpa REAL,
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
            );
        """)

        self.conn.commit()

    def insert_candidate(self, entry: dict) -> int:
        """Insert into candidates and return candidate_id."""
        name = entry.get("name")
        email = entry.get("email")
        phone = entry.get("phone") or entry.get("Phone_Number")

        self.cursor.execute(
            """
            INSERT INTO candidates (name, email, phone)
            VALUES (?, ?, ?);
            """,
            (name, email, phone),
        )
        self.conn.commit()
        return self.cursor.lastrowid  # id of this candidate

    def insert_skills(self, candidate_id: int, entry: dict):
        """Insert skills + applied_skills arrays."""
        skills_list = entry.get("skills", [])
        applied_skills_list = entry.get("applied_skills", [])

        # normal skills
        for skill in skills_list:
            self.cursor.execute(
                """
                INSERT INTO skills (candidate_id, name, category)
                VALUES (?, ?, ?);
                """,
                (candidate_id, skill.get("name"), skill.get("category")),
            )

        # applied skills (stored in same table; only data differs)
        for skill in applied_skills_list:
            self.cursor.execute(
                """
                INSERT INTO skills (candidate_id, name, category)
                VALUES (?, ?, ?);
                """,
                (candidate_id, skill.get("name"), skill.get("category")),
            )

        self.conn.commit()

    def insert_experience(self, candidate_id: int, entry: dict):
        for exp in entry.get("experience", []):
            self.cursor.execute(
                """
                INSERT INTO experience (
                    candidate_id, title, company,
                    start_year, start_month,
                    end_year, end_month,
                    duration_months
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    candidate_id,
                    exp.get("title"),
                    exp.get("company"),
                    exp.get("start_year"),
                    exp.get("start_month"),
                    exp.get("end_year"),
                    exp.get("end_month"),
                    exp.get("duration_months"),
                ),
            )
        self.conn.commit()

    def insert_projects(self, candidate_id: int, entry: dict):
        for proj in entry.get("projects", []):
            self.cursor.execute(
                """
                INSERT INTO projects (
                    candidate_id, title,
                    start_year, start_month,
                    end_year, end_month
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    candidate_id,
                    proj.get("title"),
                    proj.get("start_year"),
                    proj.get("start_month"),
                    proj.get("end_year"),
                    proj.get("end_month"),
                ),
            )
        self.conn.commit()

    def insert_education(self, candidate_id: int, entry: dict):
        for edu in entry.get("education", []):
            self.cursor.execute(
                """
                INSERT INTO education (
                    candidate_id, degree, institution,
                    graduation_year, gpa
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    candidate_id,
                    edu.get("degree"),
                    edu.get("institution"),
                    edu.get("graduation_year"),
                    edu.get("gpa"),
                ),
            )
        self.conn.commit()

    def insert_one_resume(self, entry: dict):
        """Insert one JSON resume into all tables."""
        try:
            candidate_id = self.insert_candidate(entry)
            self.insert_skills(candidate_id, entry)
            self.insert_experience(candidate_id, entry)
            self.insert_projects(candidate_id, entry)
            self.insert_education(candidate_id, entry)
        except sqlite3.IntegrityError as e:
            print("Duplicate candidate or other integrity error:", e)
            # Optionally, fetch existing id instead:
            email = entry.get("email")
            self.cursor.execute("SELECT id FROM candidates WHERE email = ?;", (email,))
            row = self.cursor.fetchone()
            if row:
                candidate_id = row[0]
            else:
                raise
        

    def insert_many_resumes(self, data: list):
        """data is a list of JSON dicts."""
        for entry in data:
            self.insert_one_resume(entry)

    def close(self):
        self.conn.close()


# Usage
if __name__ == "__main__":
    # data = extract_resume_data("Resume/resume_juanjosecarin_copy.pdf")
    # data = extract_resume_data("Resume/computer-science-internship-resume-example.pdf")
    data = extract_resume_data("Resume/EPS-Computer-Science_Resume_Sample.pdf")  # Enter the location oy your desired pdf resume file here.
    print(data)
    s = data
    with open("data.pkl", "wb") as f:
        pickle.dump(data, f)  # save data to file
    
    parsed = str2json(s)
    print(type(parsed)) # dict

    with open("response.pkl", "wb") as f:
        pickle.dump(data, f)  # save response to file
    with open("parsed_resume.pkl", "wb") as f:
        pickle.dump(parsed, f)  # save parsed dict to file


    with open("parsed_resume.pkl", "rb") as f:
        my_obj = pickle.load(f)  # load parsed dict from file
    
    # For testing with a single example:
    db = ResumeDB()
    db.create_tables()
    db.insert_many_resumes([my_obj,])  # list of dicts
    db.close()
