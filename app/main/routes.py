from datetime import datetime, timedelta
from functools import wraps
import re

from flask import abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.email import send_order_confirmation
from app.main import bp
from app.models import Category, NewsArticle, Order, OrderItem, Product, ProductVariant
from app.search import search_products


def _slugify(text):
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', (text or '').strip().lower())
    cleaned = re.sub(r'\s+', '-', cleaned)
    cleaned = re.sub(r'-+', '-', cleaned)
    return cleaned.strip('-') or 'item'


def _ensure_unique_slug(model, base_slug, current_id=None):
    slug = base_slug
    counter = 2
    while True:
        query = model.query.filter_by(slug=slug)
        if current_id is not None:
            query = query.filter(model.id != current_id)
        if query.first() is None:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def _admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        admin_username = current_app.config.get('ADMIN_USERNAME', 'admin').strip().lower()
        if current_user.username.lower() != admin_username:
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


def _load_cart():
    raw_cart = session.get('cart', {})
    cart = {}

    if isinstance(raw_cart, list):
        for product_id in raw_cart:
            key = f"{int(product_id)}|0"
            cart[key] = cart.get(key, 0) + 1
        return cart

    if isinstance(raw_cart, dict):
        for item_key, quantity in raw_cart.items():
            try:
                qty = int(quantity)
                if qty > 0:
                    cart[str(item_key)] = qty
            except (TypeError, ValueError):
                continue

    return cart


def _save_cart(cart):
    session['cart'] = cart
    session.modified = True


def _cart_count(cart=None):
    cart = cart if cart is not None else _load_cart()
    return sum(cart.values())


def _wants_json():
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']
    )


def _parse_cart_key(item_key):
    text = str(item_key)
    if '|' in text:
        p, v = text.split('|', 1)
        return int(p), int(v)
    return int(text), 0


def _resolve_variant(product, variant_id):
    if variant_id:
        variant = db.session.get(ProductVariant, variant_id)
        if not variant or variant.product_id != product.id:
            return None
        return variant

    if product.variants:
        return product.variants[0]

    return None


def _price_for(product, variant):
    if variant:
        return (product.price or 0) + (variant.price_delta or 0)
    return product.price or 0


def _available_stock(product, variant):
    if variant:
        return variant.stock
    return product.stock or 0


def _build_cart_details():
    cart = _load_cart()
    if not cart:
        return [], 0, 0

    items = []
    total = 0
    total_quantity = 0

    for item_key, quantity in cart.items():
        try:
            product_id, variant_id = _parse_cart_key(item_key)
        except ValueError:
            continue

        product = db.session.get(Product, product_id)
        if not product:
            continue

        variant = db.session.get(ProductVariant, variant_id) if variant_id else None
        unit_price = _price_for(product, variant)
        subtotal = unit_price * quantity
        total += subtotal
        total_quantity += quantity

        items.append(
            {
                'key': item_key,
                'product': product,
                'variant': variant,
                'quantity': quantity,
                'unit_price': unit_price,
                'subtotal': subtotal,
            }
        )

    return items, total, total_quantity


def _json_cart_response(success, message, status=200):
    return jsonify({'success': success, 'message': message, 'cart_count': _cart_count()}), status


def _products_payload(products):
    payload = []
    for p in products:
        payload.append(
            {
                'id': p.id,
                'name': p.name,
                'description': p.description or '',
                'price': p.price or 0,
                'stock': p.stock or 0,
                'image_url': p.image_url or '',
                'category_slug': p.category.slug if p.category else '',
            }
        )
    return payload


@bp.route('/')
@bp.route('/index')
def index():
    selected_slug = request.args.get('category', '').strip().lower()
    categories = Category.query.order_by(Category.name.asc()).all()
    products_query = Product.query

    if selected_slug:
        category = Category.query.filter_by(slug=selected_slug).first()
        if category:
            products_query = products_query.filter(Product.category_id == category.id)

    products = products_query.order_by(Product.id.desc()).all()

    return render_template(
        'index.html',
        title='Cua hang Cong nghe',
        products=products,
        categories=categories,
        selected_category_slug=selected_slug,
    )


@bp.route('/categories')
def categories_page():
    categories = Category.query.order_by(Category.name.asc()).all()
    featured = Product.query.order_by(Product.id.desc()).limit(24).all()
    return render_template('categories.html', title='Danh muc', categories=categories, featured=featured)


@bp.route('/categories/<slug>')
def category_detail(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    products = Product.query.filter_by(category_id=category.id).order_by(Product.id.desc()).all()
    return render_template('category_detail.html', title=category.name, category=category, products=products)


@bp.route('/api/categories/<slug>/products')
def category_products_api(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    products = Product.query.filter_by(category_id=category.id).order_by(Product.id.desc()).all()
    return jsonify({'category': {'name': category.name, 'slug': category.slug}, 'products': _products_payload(products)})


@bp.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    product = Product.query.get_or_404(id)
    variant_id = request.form.get('variant_id', type=int)
    variant = _resolve_variant(product, variant_id)

    if variant_id and variant is None:
        if _wants_json():
            return _json_cart_response(False, 'Model khong hop le.', 400)
        flash('Model khong hop le.', 'danger')
        return redirect(request.referrer or url_for('main.product_detail', id=id))

    available = _available_stock(product, variant)
    if available <= 0:
        if _wants_json():
            return _json_cart_response(False, 'San pham/model da het hang.', 400)
        flash('San pham/model da het hang.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

    cart = _load_cart()
    key = f"{product.id}|{variant.id if variant else 0}"
    current_qty = cart.get(key, 0)

    if current_qty >= available:
        if _wants_json():
            return _json_cart_response(False, 'Ban da them toi da so luong ton kho.', 400)
        flash('Ban da them toi da so luong ton kho.', 'warning')
        return redirect(request.referrer or url_for('main.index'))

    cart[key] = current_qty + 1
    _save_cart(cart)

    if _wants_json():
        return _json_cart_response(True, 'Da them vao gio hang!')

    flash('Da them vao gio hang!', 'success')
    return redirect(request.referrer or url_for('main.index'))


@bp.route('/buy_now/<int:id>', methods=['POST'])
def buy_now(id):
    product = Product.query.get_or_404(id)
    variant_id = request.form.get('variant_id', type=int)
    variant = _resolve_variant(product, variant_id)

    if variant_id and variant is None:
        flash('Model khong hop le.', 'danger')
        return redirect(url_for('main.product_detail', id=id))

    available = _available_stock(product, variant)
    if available <= 0:
        flash('San pham/model da het hang.', 'danger')
        return redirect(url_for('main.product_detail', id=id))

    key = f"{product.id}|{variant.id if variant else 0}"
    _save_cart({key: 1})
    flash('Da chuyen sang gio hang. Ban co the thanh toan ngay.', 'success')
    return redirect(url_for('main.cart'))


@bp.route('/remove_from_cart/<path:item_key>', methods=['POST'])
def remove_from_cart(item_key):
    cart = _load_cart()
    if item_key in cart:
        cart.pop(item_key)
        _save_cart(cart)
        flash('Da xoa san pham khoi gio hang.', 'info')
    return redirect(url_for('main.cart'))


@bp.route('/cart')
def cart():
    cart_items, total, total_quantity = _build_cart_details()
    return render_template('cart.html', title='Gio hang', cart_items=cart_items, total=total, total_quantity=total_quantity)


@bp.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.index'))
    products = search_products(query)
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template(
        'index.html',
        title='Ket qua tim kiem',
        products=products,
        query=query,
        categories=categories,
        selected_category_slug='',
    )


@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items, total, _ = _build_cart_details()
    if not cart_items:
        flash('Gio hang trong!', 'warning')
        return redirect(url_for('main.index'))

    out_of_stock = []
    for item in cart_items:
        available = _available_stock(item['product'], item['variant'])
        if item['quantity'] > available:
            label = item['product'].name
            if item['variant']:
                label += f" ({item['variant'].label})"
            out_of_stock.append(f"{label} con {available}")

    if out_of_stock:
        flash('Khong du ton kho: ' + '; '.join(out_of_stock), 'danger')
        return redirect(url_for('main.cart'))

    order = Order(user_id=current_user.id, total_amount=total)
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        product = item['product']
        variant = item['variant']
        quantity = item['quantity']
        unit_price = item['unit_price']

        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                variant_id=variant.id if variant else None,
                variant_label=variant.label if variant else None,
                quantity=quantity,
                unit_price=unit_price,
            )
        )

        if variant:
            variant.stock -= quantity
        else:
            product.stock = (product.stock or 0) - quantity

    db.session.commit()

    send_order_confirmation(current_user, order)
    _save_cart({})

    flash(f'Dat hang thanh cong! Ma don: #{order.id:06d}', 'success')
    return redirect(url_for('main.order_detail', order_id=order.id))


@bp.route('/orders')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', title='Lich su don hang', orders=orders)


@bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    admin_username = current_app.config.get('ADMIN_USERNAME', 'admin').strip().lower()
    is_admin = current_user.username.lower() == admin_username
    if order.user_id != current_user.id and not is_admin:
        abort(403)
    return render_template('order_detail.html', title=f'Don #{order.id:06d}', order=order)


@bp.route('/admin')
@_admin_required
def admin_dashboard():
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=6)
    start_dt = datetime.combine(start_date, datetime.min.time())

    grouped = (
        db.session.query(func.date(Order.created_at), func.count(Order.id))
        .filter(Order.created_at >= start_dt)
        .group_by(func.date(Order.created_at))
        .all()
    )
    daily_map = {str(day): total for day, total in grouped}

    labels = []
    values = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        key = day.isoformat()
        labels.append(day.strftime('%d/%m'))
        values.append(int(daily_map.get(key, 0)))

    inventory_products = Product.query.order_by(Product.name.asc()).all()
    total_orders_7d = sum(values)

    return render_template(
        'admin_dashboard.html',
        title='Quan tri',
        labels=labels,
        values=values,
        total_orders_7d=total_orders_7d,
        inventory_products=inventory_products,
    )


@bp.route('/admin/categories', methods=['GET', 'POST'])
@_admin_required
def admin_categories():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if name:
            slug = _ensure_unique_slug(Category, _slugify(name))
            db.session.add(Category(name=name, slug=slug))
            db.session.commit()
            flash('Da tao category.', 'success')
        return redirect(url_for('main.admin_categories'))

    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template('admin_categories.html', title='CRUD Category', categories=categories)


@bp.route('/admin/categories/<int:category_id>/update', methods=['POST'])
@_admin_required
def admin_category_update(category_id):
    category = Category.query.get_or_404(category_id)
    name = (request.form.get('name') or '').strip()
    if name:
        category.name = name
        category.slug = _ensure_unique_slug(Category, _slugify(name), current_id=category.id)
        db.session.commit()
        flash('Da cap nhat category.', 'success')
    return redirect(url_for('main.admin_categories'))


@bp.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@_admin_required
def admin_category_delete(category_id):
    category = Category.query.get_or_404(category_id)
    Product.query.filter_by(category_id=category.id).update({'category_id': None})
    db.session.delete(category)
    db.session.commit()
    flash('Da xoa category.', 'info')
    return redirect(url_for('main.admin_categories'))


@bp.route('/admin/products', methods=['GET', 'POST'])
@_admin_required
def admin_products():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if name:
            product = Product(
                name=name,
                category_id=request.form.get('category_id', type=int),
                price=request.form.get('price', type=float) or 0,
                description=(request.form.get('description') or '').strip(),
                image_url=(request.form.get('image_url') or '').strip(),
                stock=request.form.get('stock', type=int) or 0,
            )
            db.session.add(product)
            db.session.commit()
            flash('Da tao product.', 'success')
        return redirect(url_for('main.admin_products'))

    products = Product.query.order_by(Product.id.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template('admin_products.html', title='CRUD Product', products=products, categories=categories)


@bp.route('/admin/products/<int:product_id>/update', methods=['POST'])
@_admin_required
def admin_product_update(product_id):
    product = Product.query.get_or_404(product_id)
    product.name = (request.form.get('name') or product.name).strip()
    product.category_id = request.form.get('category_id', type=int)
    product.price = request.form.get('price', type=float) or 0
    product.description = (request.form.get('description') or '').strip()
    product.image_url = (request.form.get('image_url') or '').strip()
    product.stock = request.form.get('stock', type=int) or 0
    db.session.commit()
    flash('Da cap nhat product.', 'success')
    return redirect(url_for('main.admin_products'))


@bp.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@_admin_required
def admin_product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Da xoa product.', 'info')
    return redirect(url_for('main.admin_products'))


@bp.route('/admin/variants', methods=['GET', 'POST'])
@_admin_required
def admin_variants():
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        label = (request.form.get('label') or '').strip()
        if product_id and label:
            sku = (request.form.get('sku') or '').strip() or f"SKU-{product_id}-{int(datetime.utcnow().timestamp())}"
            variant = ProductVariant(
                product_id=product_id,
                label=label,
                price_delta=request.form.get('price_delta', type=float) or 0,
                stock=request.form.get('stock', type=int) or 0,
                sku=sku,
            )
            db.session.add(variant)
            db.session.commit()
            flash('Da tao variant.', 'success')
        return redirect(url_for('main.admin_variants'))

    variants = ProductVariant.query.order_by(ProductVariant.id.desc()).all()
    products = Product.query.order_by(Product.name.asc()).all()
    return render_template('admin_variants.html', title='CRUD Variant', variants=variants, products=products)


@bp.route('/admin/variants/<int:variant_id>/update', methods=['POST'])
@_admin_required
def admin_variant_update(variant_id):
    variant = ProductVariant.query.get_or_404(variant_id)
    variant.product_id = request.form.get('product_id', type=int) or variant.product_id
    variant.label = (request.form.get('label') or variant.label).strip()
    variant.price_delta = request.form.get('price_delta', type=float) or 0
    variant.stock = request.form.get('stock', type=int) or 0
    variant.sku = (request.form.get('sku') or variant.sku).strip()
    db.session.commit()
    flash('Da cap nhat variant.', 'success')
    return redirect(url_for('main.admin_variants'))


@bp.route('/admin/variants/<int:variant_id>/delete', methods=['POST'])
@_admin_required
def admin_variant_delete(variant_id):
    variant = ProductVariant.query.get_or_404(variant_id)
    db.session.delete(variant)
    db.session.commit()
    flash('Da xoa variant.', 'info')
    return redirect(url_for('main.admin_variants'))


@bp.route('/admin/news', methods=['GET', 'POST'])
@_admin_required
def admin_news():
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        if title:
            base_slug = _slugify(request.form.get('slug') or title)
            slug = _ensure_unique_slug(NewsArticle, base_slug)
            post = NewsArticle(
                title=title,
                slug=slug,
                summary=(request.form.get('summary') or '').strip(),
                content=(request.form.get('content') or '').strip(),
                image_url=(request.form.get('image_url') or '').strip(),
                published_at=datetime.utcnow(),
            )
            db.session.add(post)
            db.session.commit()
            flash('Da tao bai viet.', 'success')
        return redirect(url_for('main.admin_news'))

    posts = NewsArticle.query.order_by(NewsArticle.published_at.desc()).all()
    return render_template('admin_news.html', title='CRUD News', posts=posts)


@bp.route('/admin/news/<int:news_id>/update', methods=['POST'])
@_admin_required
def admin_news_update(news_id):
    post = NewsArticle.query.get_or_404(news_id)
    title = (request.form.get('title') or post.title).strip()
    base_slug = _slugify(request.form.get('slug') or title)

    post.title = title
    post.slug = _ensure_unique_slug(NewsArticle, base_slug, current_id=post.id)
    post.summary = (request.form.get('summary') or '').strip()
    post.content = (request.form.get('content') or '').strip()
    post.image_url = (request.form.get('image_url') or '').strip()

    db.session.commit()
    flash('Da cap nhat bai viet.', 'success')
    return redirect(url_for('main.admin_news'))


@bp.route('/admin/news/<int:news_id>/delete', methods=['POST'])
@_admin_required
def admin_news_delete(news_id):
    post = NewsArticle.query.get_or_404(news_id)
    db.session.delete(post)
    db.session.commit()
    flash('Da xoa bai viet.', 'info')
    return redirect(url_for('main.admin_news'))


@bp.route('/news')
def news_list():
    posts = NewsArticle.query.order_by(NewsArticle.published_at.desc()).all()
    return render_template('news.html', title='Tin tuc', posts=posts)


@bp.route('/news/<slug>')
def news_detail(slug):
    post = NewsArticle.query.filter_by(slug=slug).first_or_404()
    latest = NewsArticle.query.filter(NewsArticle.id != post.id).order_by(NewsArticle.published_at.desc()).limit(5).all()
    return render_template('news_detail.html', title=post.title, post=post, latest=latest)


@bp.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    related_products = Product.query.filter(Product.id != id).limit(4).all()
    return render_template('product_detail.html', title=product.name, product=product, related_products=related_products)
