import csv
from openai import OpenAI
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
DB_PATH = "local_database.db"

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found. Create a .env file using .env.example.")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)



def create_query(natural_text: str) -> str:
    """
    Convert natural language into a SAFE SQL query
    compatible with the database schema defined in ResumeDB.
    """

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        max_tokens=300,
        messages=[
            {
                "role": "system",
                "content": """
You are an SQL Query Generator for an Applicant Tracking Database.

### DATABASE SCHEMA YOU MUST FOLLOW

Tables:

1) candidates(id, name, email, phone)
2) skills(id, candidate_id, name, category)
3) experience(id, candidate_id, title, company, start_year, start_month, end_year, end_month, duration_months)
4) projects(id, candidate_id, title, start_year, start_month, end_year, end_month)
5) education(id, candidate_id, degree, institution, graduation_year, gpa)

### RULES FOR OUTPUT:

- RESPOND **ONLY WITH RAW SQL QUERY** (NO explanations, no markdown, no text).
- Query MUST be valid SQLite SQL.
- Use correct table & column names exactly as listed.
- NEVER produce destructive queries unless the user explicitly asks:
  * NO: DROP, DELETE, UPDATE, TRUNCATE.
  * Allowed ONLY if explicitly requested.
- Prefer SELECT queries returning candidate_id, names, or joined info.
- When matching skill names, ALWAYS use a case-insensitive partial match:
  Use: LOWER(s.name) LIKE '%' || LOWER(<skill>) || '%'
  NEVER use equality (=) for skill name matching.
- Use JOIN when necessary (skills, experience, projects, education).
- If user intent is unclear, make a reasonable guess.

- When returning skills for each candidate:
  Use GROUP_CONCAT(s.name, ', ') when DISTINCT is not required.
  Use GROUP_CONCAT(DISTINCT s.name) when DISTINCT is required.
  Never generate GROUP_CONCAT(DISTINCT s.name, ', ') because it is invalid SQLite syntax.

- Do NOT return separate rows for each skill.
- Every candidate must appear only once in the result.

- The query MUST be compatible with SQLite.
- For SQLite, NEVER use:
  GROUP_CONCAT(DISTINCT column, separator)

- If DISTINCT is required with GROUP_CONCAT, use:
  GROUP_CONCAT(DISTINCT column)

- If a custom separator is required together with DISTINCT, use:
  REPLACE(GROUP_CONCAT(DISTINCT column), ',', ', ')

- Before generating the final answer, verify that the query is valid SQLite syntax.


### GOAL
Convert user's natural language into 1 single valid SQL query.
"""
            },
            {"role": "user", "content": natural_text}
        ]
    )

    # Return SQL query as string
    return response.choices[0].message.content.strip()

class ResumeDB:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")  # enable FKs in SQLite
        self.cursor = self.conn.cursor()
    
    def run_query(self, query: str):
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
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



conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")  # enable FKs in SQLite
cursor = conn.cursor()


# print(cursor.execute(create_query("Show me all candidates who know Python")).fetchall())

def run_query_with_headers(query: str):
    clean_query = query.replace("```sql", "").replace("```", "").strip()
    cursor.execute(clean_query)

    # Fetch column names
    headers = [desc[0] for desc in cursor.description]
    # Fetch rows
    rows = cursor.fetchall()
    # Combine headers + rows
    return [headers] + rows

query = create_query(input("Enter you query: "))
'''
Query example:
Show me all candidates who know Angular and Django and also show how number of projects they have worked on
Tell me the total number of candidated already present in the database.
'''
print("Generated SQL Query:")
print(query)

data = run_query_with_headers(query)
print("Raw Query Data:")
print(data)

print("Query Results:")
for row in data:
    print(row)

def update_csv(Textual_NL_query):
    query = create_query(Textual_NL_query)
    data = run_query_with_headers(query)
    with open('candidates_skills.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for row in data:
            writer.writerow(row)


with open('candidates_skills.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    for row in data:
        writer.writerow(row)