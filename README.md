# Quizz Platform

This repository contains a minimal implementation of a cloud-based school quiz preparation platform. It offers:

- Multi-user authentication for students and teachers.
- CMS for teachers to upload textbooks (as plain text or PDF) and generate quizzes.
- Uploaded documents are automatically converted to clean UTF-8 text before quiz
  generation.
- AI-assisted quiz generation powered by OpenAI with a local fallback algorithm.
- Multiple quiz formats (currently short answer with extensible design).
- Responsive interface built with Bootstrap.
- Student progress analytics using Chart.js.

The app uses Flask, SQLite, and Flask-Login. Uploaded files are stored under the instance folder. Modify `DATABASE_URL` and `UPLOAD_FOLDER` environment variables to integrate with cloud services. Set `OPENAI_API_KEY` to enable AI-powered quiz generation using OpenAI.

New environment variables introduced in v0.2:

```
OPENAI_API_KEY=
AWS_S3_BUCKET=
REDIS_URL=redis://localhost:6379/0
```

Use `make dev` to run the Flask server, Celery worker and Tailwind watcher during development.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=manage.py
export OPENAI_API_KEY=<your-api-key>
flask run
```

The application will be available at `http://localhost:5000`.
