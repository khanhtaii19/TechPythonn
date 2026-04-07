import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from flask_mail import Mail
from flask_wtf import CSRFProtect
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

mail = Mail()
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login' # Trang hướng hướng khi chưa đăng nhập
csrf = CSRFProtect()


def _ensure_legacy_schema_columns():
    engine = db.engine
    inspector = inspect(engine)

    try:
        tables = set(inspector.get_table_names())
    except SQLAlchemyError:
        return

    def add_missing_columns(conn, table_name, columns):
        try:
            existing = {col['name'] for col in inspect(conn).get_columns(table_name)}
        except SQLAlchemyError:
            return

        for column_name, ddl in columns:
            if column_name in existing:
                continue
            try:
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))
            except SQLAlchemyError:
                continue

    with engine.begin() as conn:
        if 'product_variant' in tables:
            add_missing_columns(
                conn,
                'product_variant',
                [
                    ('name', 'VARCHAR(128) NULL'),
                    ('description', 'TEXT NULL'),
                    ('price', 'FLOAT NULL'),
                    ('color', 'VARCHAR(64) NULL'),
                    ('image_url', 'VARCHAR(256) NULL'),
                ],
            )

        if 'orders' in tables:
            add_missing_columns(
                conn,
                'orders',
                [
                    ('recipient_name', 'VARCHAR(120) NULL'),
                    ('phone', 'VARCHAR(32) NULL'),
                    ('city', 'VARCHAR(120) NULL'),
                    ('ward', 'VARCHAR(120) NULL'),
                    ('district', 'VARCHAR(120) NULL'),
                    ('address_line', 'VARCHAR(255) NULL'),
                    ('note', 'TEXT NULL'),
                    ('payment_method', 'VARCHAR(64) NULL'),
                ],
            )


def _cleanup_products_once(app):
    if str(app.config.get('CLEANUP_PRODUCTS_ON_START', '0')).lower() not in {'1', 'true', 'yes'}:
        return

    marker_path = os.path.join(app.instance_path, 'cleanup_products_done.txt')
    if os.path.exists(marker_path):
        return

    from app.models import OrderItem, Product

    try:
        keep_rows = db.session.query(Product.id).order_by(Product.id.desc()).limit(20).all()
        keep_ids = {row[0] for row in keep_rows}

        remove_rows = db.session.query(Product.id).filter(~Product.id.in_(keep_ids)).all() if keep_ids else []
        remove_ids = [row[0] for row in remove_rows]

        removed_order_items = 0
        removed_products = 0

        if remove_ids:
            removed_order_items = (
                OrderItem.query.filter(OrderItem.product_id.in_(remove_ids))
                .delete(synchronize_session=False)
            )
            remove_products = Product.query.filter(Product.id.in_(remove_ids)).all()
            removed_products = len(remove_products)
            for product in remove_products:
                db.session.delete(product)
            db.session.commit()

        os.makedirs(app.instance_path, exist_ok=True)
        with open(marker_path, 'w', encoding='utf-8') as marker_file:
            marker_file.write(
                f"cleanup_done=1\nkept_products=20\nremoved_products={removed_products}\nremoved_order_items={removed_order_items}\n"
            )
    except SQLAlchemyError:
        db.session.rollback()
        return

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
            _ensure_legacy_schema_columns()
            _cleanup_products_once(app)
        except SQLAlchemyError:
            pass

    return app

from app import models
