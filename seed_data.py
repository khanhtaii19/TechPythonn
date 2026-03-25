"""Script để seed dữ liệu mẫu vào database"""
from app import create_app, db
from app.models import Product

app = create_app()

with app.app_context():
    # Xóa dữ liệu cũ (tùy chọn)
    # Product.query.delete()
    
    # Tạo các sản phẩm mẫu
    products = [
        Product(
            name='iPhone 15 Pro Max',
            price=29990000,
            description='Điện thoại flagship Apple với màn hình OLED 6.7 inch, chip A17 Pro, camera 48MP',
            image_url='/app/static/images/product/iphone15.png',
            stock=15
        ),
        Product(
            name='MacBook Pro M3',
            price=49990000,
            description='Laptop chuyên nghiệp Apple với chip M3, 8GB RAM, SSD 512GB',
            image_url='https://via.placeholder.com/300x400?text=MacBook+Pro+M3',
            stock=8
        ),
        Product(
            name='Samsung Galaxy S24',
            price=18990000,
            description='Flagship Samsung với màn hình Dynamic AMOLED 120Hz, chip Snapdragon 8 Gen 3',
            image_url='https://via.placeholder.com/300x400?text=Galaxy+S24',
            stock=20
        ),
        Product(
            name='iPad Air M2',
            price=16990000,
            description='Tablet mạnh mẽ với chip M2, màn hình Liquid Retina 11 inch, hỗ trợ Apple Pencil',
            image_url='https://via.placeholder.com/300x400?text=iPad+Air+M2',
            stock=12
        ),
        Product(
            name='Sony WH-1000XM5 Headphones',
            price=7990000,
            description='Tai nghe không dây cao cấp với ANC tốt nhất, thời lượng pin 40 giờ',
            image_url='https://via.placeholder.com/300x400?text=Sony+Headphones',
            stock=25
        ),
        Product(
            name='Dell XPS 15',
            price=42990000,
            description='Laptop cao cấp Windows với Intel Core i9, RTX 4090, màn hình OLED 4K',
            image_url='https://via.placeholder.com/300x400?text=Dell+XPS+15',
            stock=6
        ),
        Product(
            name='Google Pixel 8 Pro',
            price=21990000,
            description='Smartphone Google với AI photography, chip Tensor G3, camera 50MP',
            image_url='https://via.placeholder.com/300x400?text=Pixel+8+Pro',
            stock=18
        ),
        Product(
            name='Apple Watch Ultra',
            price=12990000,
            description='Smartwatch bền bỉ với thiết kế titanium, pin 36 giờ, chống nước 100m',
            image_url='https://via.placeholder.com/300x400?text=Apple+Watch+Ultra',
            stock=14
        ),
    ]
    
    # Thêm vào database
    for product in products:
        # Kiểm tra xem sản phẩm đã tồn tại chưa
        existing = Product.query.filter_by(name=product.name).first()
        if not existing:
            db.session.add(product)
    
    db.session.commit()
    print(f"✅ Đã thêm {len(products)} sản phẩm mẫu vào database")
