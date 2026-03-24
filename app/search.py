from flask import request
from app.models import Product

def search_products(query):
    # Tìm kiếm theo tên hoặc mô tả sản phẩm (không phân biệt hoa thường)
    results = Product.query.filter(
        (Product.name.ilike(f"%{query}%")) | 
        (Product.description.ilike(f"%{query}%"))
    ).all()
    return results