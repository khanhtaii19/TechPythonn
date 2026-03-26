from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from flask_mail import Mail
from flask_wtf import CSRFProtect
from sqlalchemy.exc import SQLAlchemyError

mail = Mail()
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login' # Trang hướng hướng khi chưa đăng nhập
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Đăng ký các Blueprint
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    @app.template_filter('zfill')
    def zfill_filter(s, width):
      return str(s).zfill(width)

    @app.context_processor
    def inject_common_data():
        from app.models import Category
        try:
            categories = Category.query.order_by(Category.name.asc()).all()
        except SQLAlchemyError:
            categories = []
        return {'nav_categories': categories}

    # Keep auth pages usable even when user forgets to run migrations.
    with app.app_context():
        try:
            db.create_all()
        except SQLAlchemyError:
            pass

    return app

from app import models
