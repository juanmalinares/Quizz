import json
import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from quizz.app import create_app, db
from quizz.app.models import User, Document
from quizz.app.services.ai_quiz import _validate_mix, persist_quiz

@pytest.fixture(scope='function')
def app():
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        u1 = User(username='t1', password='x', role='teacher')
        u2 = User(username='t2', password='x', role='teacher')
        db.session.add_all([u1, u2])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
    os.environ.pop('DATABASE_URL')

@pytest.fixture
def client(app):
    return app.test_client()


def test_patch_document_forbidden(client, app):
    with app.app_context():
        doc = Document(filename='a.txt', uploaded_by=1)
        db.session.add(doc)
        db.session.commit()
        # login as user2
        with client.session_transaction() as sess:
            sess['_user_id'] = '2'
        resp = client.patch(f'/api/documents/{doc.id}', json={'friendly_name': 'X'})
        assert resp.status_code == 403


def test_validate_mix():
    q = [{'type': 'multiple_choice'}, {'type': 'multiple_choice'}]
    assert not _validate_mix(q)
    q.append({'type': 'true_false'})
    q.append({'type': 'short_answer'})
    assert _validate_mix(q)


def test_persist_quiz_length(app):
    with app.app_context():
        doc = Document(filename='b.txt', uploaded_by=1, desired_q=2)
        db.session.add(doc)
        db.session.commit()
        data = {
            'name': 'Test Quiz',
            'questions': [
                {'type': 'multiple_choice', 'text': 'q1', 'options': ['a','b'], 'answer':0},
                {'type': 'short_answer', 'text': 'q2', 'answer':'x'},
                {'type': 'true_false', 'text': 'q3', 'answer':True}
            ]
        }
        quiz = persist_quiz(data, doc.id)
        assert len(quiz.questions) == 2
