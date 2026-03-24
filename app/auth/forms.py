from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    remember_me = BooleanField('Ghi nhớ đăng nhập')
    submit = SubmitField('Đăng Nhập')

class RegistrationForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    password_confirm = PasswordField('Nhập lại mật khẩu', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Đăng Ký')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Tên đăng nhập đã tồn tại.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email này đã được sử dụng.')