from sqlalchemy import or_

from app.models import Category, Product


def search_products(query):
    category_ids = [c.id for c in Category.query.filter(Category.name.ilike(f'%{query}%')).all()]

    conditions = [
        Product.name.ilike(f'%{query}%'),
        Product.description.ilike(f'%{query}%'),
    ]
    if category_ids:
        conditions.append(Product.category_id.in_(category_ids))

    q = Product.query.filter(or_(*conditions))
    return q.all()
