"""Seed categories, products, variants, and news data."""

from app import create_app, db
from app.models import Category, NewsArticle, Product, ProductVariant

app = create_app()

CATEGORY_NAMES = [
    'Điện Thoại',
    'Laptop',
    'Máy Tính Bảng',
    'Đồng Hồ Thông Minh',
    'Phụ Kiện',
]

PRODUCT_PREFIXES = {
    'Điện Thoại': ['Samsung Galaxy S26 Ultra', 'iPhone 17 Pro Max', 'Google Pixel 10 Pro', 'Samsung Galaxy Z Fold 7', 'OnePlus 15'],
    'Laptop': ['MacBook Air M5', 'Dell XPS 14 (2026)', 'MacBook Pro 14/16 (M5 Pro/Max)', 'ASUS Zenbook S14', 'ASUS ROG Zephyrus G14 (2026)'],
    'Máy Tính Bảng': ['iPad Pro M5 (OLED)', 'Samsung Galaxy Tab S11 Ultra', 'iPad Air M4 (2026)', 'Microsoft Surface Pro 12', 'OnePlus Pad 3'],
    'Đồng Hồ Thông Minh': ['Apple Watch Series 11', 'Samsung Galaxy Watch 8', 'Apple Watch Ultra 3', 'Garmin Venu 4', 'Google Pixel Watch 4'],
    'Phụ Kiện': ['Sony WH-1000XM6', 'Anker Nano 45W Charger', 'Logitech MX Master 3S (Gen 2)', 'Apple AirPods Pro (Gen 3)', 'Samsung T9 Portable SSD'],
}

NEWS_DATA = [
    {
        'title': 'Xu hướng công nghệ 2026: Khi AI trở thành "Bản sao" kỹ thuật số',
        'slug': 'xu-huong-cong-nghe-2026-ai-ca-nhan-hoa',
        'summary': 'Bước sang năm 2026, trí tuệ nhân tạo (AI) không còn là một công cụ xa lạ trên đám mây mà đã thực sự "hòa tan" vào đời sống cá nhân qua các thiết bị đầu cuối. Trọng tâm của kỷ nguyên này chính là AI cá nhân hóa (Personalized AI).',
        'content': 'Trong nam 2026, AI tap trung vao tro ly ca nhan, toi uu pin va camera, va nang cao bao mat cho nguoi dung.',
    },
    {
        'title': 'Huong dan chon laptop cho lap trinh vien',
        'slug': 'huong-dan-chon-laptop-cho-lap-trinh-vien',
        'summary': 'Nhung tieu chi quan trong khi chon laptop cho code va devops.',
        'content': 'Uu tien CPU nhieu nhan, RAM toi thieu 16GB, SSD NVMe, man hinh tot va ban phim on dinh de lam viec lau dai.',
    },
    {
        'title': '5 meo keo dai tuoi tho pin dien thoai',
        'slug': '5-meo-keo-dai-tuoi-tho-pin-dien-thoai',
        'summary': 'Toi uu thoi quen sac pin va cai dat de su dung ben bi hon.',
        'content': 'Khong de pin 0% thuong xuyen, han che nhiet do cao, su dung sac chinh hang va theo doi ung dung ton pin.',
    },
    {
        'title': 'So sanh tablet cho hoc tap va ghi chu',
        'slug': 'so-sanh-tablet-cho-hoc-tap-va-ghi-chu',
        'summary': 'Nhung diem can can nhac giua cac dong tablet pho bien.',
        'content': 'Neu hoc tap, hay uu tien but, do tre thap, pin dai va he sinh thai dong bo tai lieu.',
    },
]


def slugify(text):
    return text.lower().replace(' ', '-').replace('/', '-')


with app.app_context():
    categories = {}
    for name in CATEGORY_NAMES:
        slug = slugify(name)
        cat = Category.query.filter_by(slug=slug).first()
        if not cat:
            cat = Category(name=name, slug=slug)
            db.session.add(cat)
            db.session.flush()
        categories[name] = cat

    created_products = 0
    created_variants = 0

    for cat_name in CATEGORY_NAMES:
        cat = categories[cat_name]
        prefixes = PRODUCT_PREFIXES[cat_name]

        for idx in range(1, 21):
            product_name = f"{prefixes[idx % len(prefixes)]} {cat_name} {idx:02d}"
            product = Product.query.filter_by(name=product_name).first()
            if not product:
                base_price = 1500000 + idx * 250000 + (CATEGORY_NAMES.index(cat_name) * 450000)
                product = Product(
                    name=product_name,
                    category_id=cat.id,
                    price=base_price,
                    description=f"{product_name} là sản phẩm chất lượng cao trong danh mục {cat_name}.",
                    image_url=f"https://via.placeholder.com/600x400?text={product_name.replace(' ', '+')}",
                    stock=30,
                )
                db.session.add(product)
                db.session.flush()
                created_products += 1
            else:
                product.category_id = cat.id

            variants_data = [
                ('Bản tiêu chuẩn', 'Bản tiêu chuẩn', 0, 12, 'Xám'),
                ('Màu Đen', 'Phiên bản màu đen', 150000, 10, 'Đen'),
                ('Màu Bạc / Quốc Tế', 'Phiên bản quốc tế', 300000, 8, 'Bạc'),
            ]

            for v_idx, (label, name, delta, v_stock, color) in enumerate(variants_data, start=1):
                sku = f"{cat.slug[:4].upper()}-{product.id:04d}-V{v_idx}"
                variant = ProductVariant.query.filter_by(sku=sku).first()
                if not variant:
                    variant = ProductVariant(
                        product_id=product.id,
                        label=label,
                        name=name,
                        description=f'{name} của {product_name}',
                        price=base_price + delta,
                        color=color,
                        image_url=f"https://via.placeholder.com/600x400?text={product_name.replace(' ', '+')}+{name.replace(' ', '+')}",
                        price_delta=delta,
                        stock=v_stock,
                        sku=sku,
                    )
                    db.session.add(variant)
                    created_variants += 1
                else:
                    variant.name = name
                    variant.description = f'{name} của {product_name}'
                    variant.price = base_price + delta
                    variant.color = color
                    variant.image_url = f"https://via.placeholder.com/600x400?text={product_name.replace(' ', '+')}+{name.replace(' ', '+')}"

            total_stock = sum(v[2] for v in variants_data)
            product.stock = total_stock

    created_news = 0
    for item in NEWS_DATA:
        post = NewsArticle.query.filter_by(slug=item['slug']).first()
        if not post:
            post = NewsArticle(
                title=item['title'],
                slug=item['slug'],
                summary=item['summary'],
                content=item['content'],
                image_url='https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200',
            )
            db.session.add(post)
            created_news += 1

    db.session.commit()

    total_products = Product.query.count()
    total_categories = Category.query.count()
    print(f"Seed done: +{created_products} products, +{created_variants} variants, +{created_news} news")
    print(f"Current totals: {total_categories} categories, {total_products} products")
