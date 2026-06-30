# chat_Ai_Tool

`chat_Ai_Tool` is a Streamlit private chat app with SQLite storage, user accounts, private one-to-one messaging, presence tracking, and a Gemini-powered reply helper.

## Features

- User registration and login
- Session management
- Private messaging between users
- Chat history in SQLite
- Online status based on recent activity
- Gemini AI reply suggestions
- Environment-based configuration

## Project layout

- `app.py` - Streamlit entry point
- `src/chat_ai_tool/` - application code
- `data/` - local SQLite database files
- `.env.example` - environment variable template
- `.streamlit/` - Streamlit local config and secrets template
- `.github/workflows/` - GitHub Actions CI
- `requirements.txt` - Python dependencies

## Setup

1. Create a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set your values.
4. Run the app:

   ```bash
   streamlit run app.py
   ```

## Environment variables

- `APP_NAME` - application title
- `APP_DEBUG` - enable extra debug behavior
- `SECRET_KEY` - secret used for session and security helpers
- `DATABASE_PATH` - SQLite database location
- `SESSION_TTL_MINUTES` - session lifetime in minutes
- `GEMINI_API_KEY` - Google Gemini API key
- `GEMINI_MODEL` - Gemini model name
- `GEMINI_TIMEOUT_SECONDS` - request timeout for Gemini calls
- `AI_SYSTEM_PROMPT` - optional assistant behavior prompt

## GitHub deployment

1. Create a GitHub repository.
2. Commit and push the project files.
3. GitHub Actions will run `.github/workflows/ci.yml` on push and pull requests.

## Streamlit Community Cloud deployment

1. Push the repo to GitHub.
2. Connect the repo in Streamlit Community Cloud.
3. Set the main file path to `app.py`.
4. Add the values from `.streamlit/secrets.example.toml` to your app secrets.
5. Keep SQLite for local use or single-instance deployment only.

## Streamlit config

- `.streamlit/config.toml` enables headless mode and sets a theme.
- `.streamlit/secrets.example.toml` shows the exact keys you need for local or cloud deployment.

## Notes

This first production-style version uses SQLite for simplicity. If you later need multi-user scale or horizontal deployment, we should move to PostgreSQL and external session storage.
