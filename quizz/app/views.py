import os
from flask import (render_template, redirect, url_for, flash, request,
                   send_from_directory)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Document, Quiz, Question, Option, UserQuiz
from .forms import LoginForm, RegisterForm, UploadForm
from .utils import read_document_text
from .tasks import generate_quiz as generate_quiz_task
from werkzeug.utils import secure_filename

from flask import current_app as app


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    password=generate_password_hash(form.password.data),
                    role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    docs = Document.query.filter_by(uploaded_by=current_user.id).all() if current_user.role == 'teacher' else []
    quizzes = Quiz.query.all()
    return render_template('dashboard.html', docs=docs, quizzes=quizzes)


@app.route('/api/documents/<int:id>', methods=['PATCH'])
@login_required
def api_patch_document(id):
    doc = Document.query.get_or_404(id)
    if doc.uploaded_by != current_user.id:
        return '', 403
    data = request.get_json() or {}
    if 'friendly_name' in data:
        doc.friendly_name = data['friendly_name']
    if 'instructions' in data:
        doc.instructions = data['instructions']
    if 'desired_q' in data:
        doc.desired_q = int(data['desired_q'])
    db.session.commit()
    return {'id': doc.id, 'friendly_name': doc.friendly_name}


@app.route('/api/quizzes/<int:id>', methods=['PATCH'])
@login_required
def api_patch_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    if quiz.document.uploaded_by != current_user.id:
        return '', 403
    data = request.get_json() or {}
    if 'friendly_name' in data:
        quiz.friendly_name = data['friendly_name']
    db.session.commit()
    return {'id': quiz.id, 'friendly_name': quiz.friendly_name}


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role != 'teacher':
        return redirect(url_for('dashboard'))
    form = UploadForm()
    if form.validate_on_submit():
        f = form.file.data
        filename = secure_filename(f.filename)
        ext = os.path.splitext(filename)[1].lower()
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(path)
        doc = Document(filename=filename, uploaded_by=current_user.id,
                       instructions=request.form.get('instructions'),
                       desired_q=int(request.form.get('desired_q', 10)))
        if ext == '.txt':
            doc.file_type = 'text'
        elif ext in {'.png', '.jpg', '.jpeg'}:
            doc.file_type = 'image'
            # pretend upload to S3
            doc.s3_url = f"s3://{os.getenv('AWS_S3_BUCKET','bucket')}/{filename}"
        else:
            doc.file_type = 'pdf'
        # store extracted UTF-8 content for later quiz generation
        doc.content = read_document_text(path)
        db.session.add(doc)
        db.session.commit()
        flash('File uploaded')
        return redirect(url_for('dashboard'))
    return render_template('upload.html', form=form)


@app.route('/generate_quiz/<int:doc_id>')
@login_required
def generate_quiz(doc_id):
    task = generate_quiz_task.delay(doc_id)
    flash('Quiz generation started')
    return redirect(url_for('task_status', task_id=task.id))


@app.route('/api/task_status/<task_id>')
@login_required
def task_status(task_id):
    async_result = generate_quiz_task.AsyncResult(task_id)
    return {'state': async_result.state}


@app.route('/take_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        score = 0
        for question in quiz.questions:
            ans = request.form.get(str(question.id), '').strip()
            if ans.lower() == (question.answer or '').lower():
                score += 1
        uq = UserQuiz(user_id=current_user.id, quiz_id=quiz.id, score=score)
        db.session.add(uq)
        db.session.commit()
        flash(f'You scored {score}/{len(quiz.questions)}')
        return redirect(url_for('dashboard'))
    return render_template('take_quiz.html', quiz=quiz)


@app.route('/analytics')
@login_required
def analytics():
    data = UserQuiz.query.filter_by(user_id=current_user.id).all()
    labels = [q.taken_at.strftime('%Y-%m-%d') for q in data]
    scores = [q.score for q in data]
    return render_template('analytics.html', labels=labels, scores=scores)


@app.route('/uploads/<path:filename>')
@login_required
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
