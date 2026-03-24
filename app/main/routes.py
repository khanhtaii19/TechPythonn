from flask import render_template, redirect, url_for, session, flash, request
from app.main import bp
from app.models import Product
from app import db
from app.search import search_products
from flask_login import login_required, current_user
from app.email import send_order_confirmation

@bp.route('/')
@bp.route('/index')
def index():
    products = Product.query.all()
    return render_template('index.html', title='Cửa hàng Công nghệ', products=products)

@bp.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(id)
    session.modified = True
    flash('Đã thêm sản phẩm vào giỏ hàng!')
    return redirect(url_for('main.index'))

@bp.route('/cart')
def cart():
    cart_ids = session.get('cart', [])
    products = Product.query.filter(Product.id.in_(cart_ids)).all() if cart_ids else []
    total = sum(p.price for p in products)
    return render_template('cart.html', title='Giỏ hàng', products=products, total=total)

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.index'))
    products = search_products(query)
    return render_template('index.html', title='Kết quả tìm kiếm', products=products, query=query)

@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_ids = session.get('cart', [])
    if not cart_ids:
        flash('Giỏ hàng trống!')
        return redirect(url_for('main.index'))
    
    # Ở đây bạn có thể thêm logic tạo bản ghi Order vào DB
    # Sau đó gửi email xác nhận
    send_order_confirmation(current_user)
    
    session['cart'] = [] # Xóa giỏ hàng sau khi đặt
    flash('Đặt hàng thành công! Vui lòng kiểm tra email xác nhận.')
    return redirect(url_for('main.index'))