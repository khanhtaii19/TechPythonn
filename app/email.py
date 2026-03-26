from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from app import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg),
        daemon=True,
    ).start()


def send_order_confirmation(user, order):
    send_email(
        '[TechStore] Xac nhan don hang thanh cong',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user.email],
        text_body=render_template('email/order_conf.txt', user=user, order=order),
        html_body=render_template('email/order_conf.html', user=user, order=order),
    )
