from datetime import datetime

from app import db, login
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    orders = db.relationship('Order', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    products = db.relationship('Product', backref='category', lazy='dynamic')


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True)
    name = db.Column(db.String(128), index=True)
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(256), default='default_tech.jpg')
    stock = db.Column(db.Integer)
    variants = db.relationship('ProductVariant', backref='product', lazy='select', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')


class ProductVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    label = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128), nullable=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=True)
    color = db.Column(db.String(64), nullable=True)
    image_url = db.Column(db.String(256), nullable=True)
    price_delta = db.Column(db.Float, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    sku = db.Column(db.String(64), unique=True, nullable=False, index=True)

    def final_price(self):
        if self.price is not None:
            return self.price
        return (self.product.price or 0) + (self.price_delta or 0)


class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(200), nullable=False, unique=True, index=True)
    summary = db.Column(db.String(400), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(256), nullable=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), default='PROCESSING', nullable=False)
    recipient_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    ward = db.Column(db.String(120), nullable=True)
    district = db.Column(db.String(120), nullable=True)
    address_line = db.Column(db.String(255), nullable=True)
    note = db.Column(db.Text, nullable=True)
    payment_method = db.Column(db.String(64), nullable=True)
    items = db.relationship('OrderItem', backref='order', lazy='select', cascade='all, delete-orphan')


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True, index=True)
    variant_label = db.Column(db.String(128), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    variant = db.relationship('ProductVariant')

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))
