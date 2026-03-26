from app import create_app, db
from app.models import Category, NewsArticle, Order, OrderItem, Product, ProductVariant, User

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Product': Product,
        'ProductVariant': ProductVariant,
        'NewsArticle': NewsArticle,
        'Order': Order,
        'OrderItem': OrderItem,
    }

if __name__ == '__main__':
    app.run(debug=True)
