from flask_mail import Message
from flask import current_app, render_template
from app import mail
from threading import Thread

# Gửi mail bất đồng bộ để không làm treo giao diện web
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, 
           args=(current_app._get_current_object(), msg)).start()

def send_order_confirmation(user):
    send_email('[TechStore] Xác nhận đơn hàng thành công',
               sender=current_app.config['MAIL_USERNAME'],
               recipients=[user.email],
               text_body=render_template('email/order_conf.txt', user=user),
               html_body=render_template('email/order_conf.html', user=user))