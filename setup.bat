if not exist .venv\ (
    python -m venv .venv
)
.\.venv\Scripts\activate.bat
.\.venv\bin\pip install -r requirements.txt