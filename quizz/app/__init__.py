from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from celery import Celery
import os

db = SQLAlchemy()
login_manager = LoginManager()
celery = Celery(__name__)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///quizz.db')
    app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # expose uploads path for tasks running outside app context
    os.environ.setdefault('UPLOAD_FOLDER', app.config['UPLOAD_FOLDER'])

    celery.conf.update(broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    celery.conf.update(result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))

    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    with app.app_context():
        from . import views  # noqa
        from . import tasks  # noqa
        db.create_all()

    login_manager.login_view = 'login'

    return app
