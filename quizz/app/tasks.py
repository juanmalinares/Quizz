from . import celery, db
from .services.ai_quiz import build_quiz, persist_quiz

@celery.task(bind=True)
def generate_quiz(self, doc_id):
    quiz_data = build_quiz(doc_id)
    persist_quiz(quiz_data, doc_id)
    return {'status': 'completed'}
