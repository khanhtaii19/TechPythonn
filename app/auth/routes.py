from urllib.parse import urlparse

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError, OperationalError

from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User


def _ensure_admin_account():
    username = (current_app.config.get('ADMIN_USERNAME') or '').strip()
    password = current_app.config.get('ADMIN_PASSWORD')
    email = (current_app.config.get('ADMIN_EMAIL') or '').strip()

    if not username or not password or not email:
        return

    admin_user = User.query.filter_by(username=username).first()
    if admin_user:
        return

    admin_user = User(username=username, email=email)
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('Ban da dang nhap roi.', 'info')
        return render_template('auth/login.html', title='Dang nhap', form=LoginForm()), 200

    try:
        _ensure_admin_account()
    except Exception:
        db.session.rollback()

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
        except OperationalError:
            db.session.rollback()
            flash('Co loi CSDL. Hay chay migration (flask db upgrade) roi thu lai.', 'danger')
            return redirect(url_for('auth.login'))

        # Last-resort bootstrap: allow first admin login even if admin row has not been created yet.
        if user is None:
            admin_username = (current_app.config.get('ADMIN_USERNAME') or '').strip()
            admin_password = current_app.config.get('ADMIN_PASSWORD') or ''
            admin_email = (current_app.config.get('ADMIN_EMAIL') or '').strip() or 'admin@techstore.local'
            if (
                admin_username
                and form.username.data == admin_username
                and form.password.data == admin_password
            ):
                try:
                    user = User(username=admin_username, email=admin_email)
                    user.set_password(admin_password)
                    db.session.add(user)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    user = None

        if user is None or not user.check_password(form.password.data):
            flash('Sai ten dang nhap hoac mat khau', 'danger')
            return render_template('auth/login.html', title='Dang nhap', form=form), 200

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)

    return render_template('auth/login.html', title='Dang nhap', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('Ban da dang nhap, khong can dang ky tai khoan moi.', 'info')
        return render_template('auth/register.html', title='Dang ky', form=RegistrationForm()), 200

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Chuc mung! Ban da dang ky thanh cong.', 'success')
            return render_template('auth/login.html', title='Dang nhap', form=LoginForm()), 200
        except IntegrityError:
            db.session.rollback()
            flash('Ten dang nhap hoac email da ton tai.', 'danger')
        except OperationalError:
            db.session.rollback()
            flash('Co loi CSDL. Hay chay migration (flask db upgrade) roi thu lai.', 'danger')
        except Exception:
            db.session.rollback()
            flash('Dang ky that bai do loi he thong. Thu lai sau.', 'danger')

    return render_template('auth/register.html', title='Dang ky', form=form)
