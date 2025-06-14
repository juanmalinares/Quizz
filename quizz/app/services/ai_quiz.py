import json
import os

from ..models import Document, Quiz, Question, Option, db
from ..utils import read_document_text

try:
    import openai
except Exception:  # pragma: no cover
    openai = None

SYSTEM_PROMPT = "You are a pedagogy-savvy quiz generator"


def extract_text_from(doc: Document) -> str:
    if doc.content:
        return doc.content
    path = os.path.join(os.getenv('UPLOAD_FOLDER', ''), doc.filename)
    return read_document_text(path)


def _prompt_for(doc: Document, text: str) -> str:
    return (
        f"Instructions: {doc.instructions or ''}\n" + text[:8000]
    )


def _call_openai(prompt: str):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or not openai:
        return None
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model='gpt-4o',
        temperature=0.3,
        messages=[{'role': 'system', 'content': SYSTEM_PROMPT},
                  {'role': 'user', 'content': prompt}],
    )
    return response['choices'][0]['message']['content']


def _validate_mix(questions):
    types = {q.get('type') for q in questions if 'type' in q}
    return len(types) >= 3


def build_quiz(doc_id: int):
    doc = Document.query.get(doc_id)
    text = extract_text_from(doc)
    prompt = _prompt_for(doc, text)

    attempts = 0
    result = None
    while attempts < 3:
        output = _call_openai(prompt)
        if not output:
            break
        try:
            data = json.loads(output)
            if _validate_mix(data.get('questions', [])):
                result = data
                break
        except Exception:
            pass
        attempts += 1
    if result is None:
        result = {"name": doc.friendly_name or doc.filename,
                  "questions": []}
    return result


def persist_quiz(data, doc_id: int):
    quiz = Quiz(title=data.get('name', 'Quiz'), document_id=doc_id,
                friendly_name=data.get('name'))
    db.session.add(quiz)
    questions = data.get('questions', [])[:Document.query.get(doc_id).desired_q]
    for q in questions:
        question = Question(quiz=quiz,
                            text=q.get('text') or q.get('question', ''),
                            qtype=q.get('type', 'short_answer'),
                            answer=str(q.get('answer')),
                            image=q.get('image'))
        db.session.add(question)
        opts = q.get('options') or []
        for idx, opt in enumerate(opts):
            db.session.add(Option(question=question, text=opt,
                                  is_correct=(idx == q.get('answer'))))
    db.session.commit()
    return quiz

