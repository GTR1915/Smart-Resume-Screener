# Smart Resume Screener

## 📖 Description

Recruiters often need to review hundreds or even thousands of resumes for a single position. Manually identifying the most suitable candidates can be time-consuming, inefficient, and sometimes susceptible to unintentional bias or favoritism.

**Smart Resume Screener** is an AI-powered resume screening and candidate matching system designed to automate this process. The project extracts structured information from resumes, stores it in a searchable database, and allows recruiters to describe their ideal candidate in natural language.

The system then analyzes all available resumes and identifies the candidates that best match the recruiter's requirements.

### Why This Project?

* Reduce the time spent manually reviewing resumes.
* Improve consistency in candidate evaluation.
* Minimize the impact of human bias and favoritism.
* Help recruiters quickly identify the most relevant candidates.
* Scale efficiently when handling large volumes of applications.

---

## 📋 Prerequisites

Before setting up the project, ensure that the following software is installed on your system:

### Required

* **Python 3.12** (the project was developed and tested using Python 3.12)
* **pip** (Python package manager)

### Verify Your Installation

Check your Python version:

```bash
python --version
```

Expected output:

```text
Python 3.12.x
```

Check your pip version:

```bash
pip --version
```

### Compatibility Note

While the project was developed and tested on **Python 3.12**, it may work on other recent Python versions. However, for the best compatibility and to avoid dependency-related issues, Python 3.12 is recommended.


## ⚙️ Installation & Setup


Follow these steps to set up the project on your local machine.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-folder>
```

---

### 2. Install Dependencies

Install all required Python packages using:

```bash
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

---

### 4. Add Your OpenRouter API Key

Open the newly created `.env` file and replace the placeholder value with your own OpenRouter API key:

```env
OPENROUTER_API_KEY=your_api_key_here
DB_PATH=local_database.db
```

Example:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx
DB_PATH=local_database.db
```

> 🔒 Never share your API key or upload your `.env` file to GitHub.

---

### 5. Verify Your Setup

Your project directory should now look similar to:

```text
Smart Resume Screener Project/
│
├── .env
├── .env.example
├── requirements.txt
├── automated_query_generation.py
├── CV_data_extraction_v2.py
└── Resume/
```

Once these steps are complete, you're ready to process resumes and search for candidates.

---

## 🔑 Guide on Creating Your OpenRouter API Key

This project uses OpenRouter to access AI models. Before running the project, you'll need to create your own API key.

### Step 1: Create an OpenRouter Account

Visit:

https://openrouter.ai

Sign up using your preferred authentication method (Google, GitHub, etc.).

---

### Step 2: Generate an API Key

1. Log in to your OpenRouter account.
2. Open the **Keys** section from your dashboard.
3. Click **Create Key**.
4. Give your key a name (e.g., `Smart-Resume-Screener`).
5. Copy the generated API key.

> ⚠️ Keep your API key private. Never share it publicly or commit it to GitHub.

---

### Step 3: Update Your `.env` File

Paste the generated API key into your `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
DB_PATH=local_database.db
```

---

### Troubleshooting

If you receive an error related to `OPENROUTER_API_KEY`, ensure that:

* The `.env` file exists in the project root directory.
* The API key is correctly copied without extra spaces.
* The key has not been revoked from your OpenRouter account.

---

## 🚀 Running the Project

Once you have configured your OpenRouter API key and installed the required dependencies, follow these steps to use the project.

### Step 1: Add Resume PDFs

Place all resume PDF files that you want to analyze inside the `Resume/` folder.

For convenience, three sample resumes have already been included in the repository, allowing you to test the project immediately.

```text
Resume/
├── computer-science-internship-resume-example.pdf
├── EPS-Computer-Science_Resume_Sample.pdf
└── resume_juanjosecarin_copy.pdf
```

---

### Step 2: Extract and Store Resume Data

Run:

```bash
python CV_data_extraction_v2.py
```

This script will:

* Read all PDF resumes from the `Resume/` directory.
* Extract relevant information using AI-powered parsing.
* Store the processed data in a local SQLite database.
* Automatically create `local_database.db` if it does not already exist.

> ⏳ Processing a typical 2–3 page resume takes approximately **45 seconds** depending on internet speed and API response times.

Wait until all resumes have been processed before proceeding.

---

### Step 3: Search for Candidates

Run:

```bash
python automated_query_generation.py
```

Enter your desired hiring requirements when prompted.

#### Example Queries

```text
Find candidates with Python and Machine Learning experience.
```

```text
Looking for a Computer Science student interested in AI.
```

```text
Find candidates with web development and database skills.
```

The system will search the stored resume database and return the candidates that best match the specified requirements.

---

## 🔄 Workflow Summary

```text
1. Add PDFs to Resume/
        ↓
2. Run CV_data_extraction_v2.py
        ↓
3. Resume data stored in local_database.db
        ↓
4. Run automated_query_generation.py
        ↓
5. Enter hiring requirements
        ↓
6. Receive ranked candidate matches
```

---

## 📝 Notes

* The database is created automatically if it does not exist.
* You only need to re-run `CV_data_extraction_v2.py` when new resumes are added or existing resumes are modified.
* The included sample resumes can be used for quick testing.
* Resume processing time depends on the number of resumes and API response speed.
