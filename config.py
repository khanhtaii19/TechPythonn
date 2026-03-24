import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '1a317c1a31f8d1badf45b0e7f4361ee454ad945bfb412cea40a844993973101b7060b51df778ef9c2cb8584b4535d5ff924a4210c4692b5694a6c9848e4b5099'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/tech_store_db'
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'phamkhanhtaii@gmail.com' # Email của bạn
    MAIL_PASSWORD = '123456' # App Password của Google