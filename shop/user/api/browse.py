from flask import jsonify, request
from shop.models import Category, Product, User  # 🔥 User import karna zaroori hai Magic Query ke liye
from shop.utils.api_response import error_response
from shop.seller.api.helpers import serialize_seller_product

def get_categories_action():
    try:
        categories = Category.query.filter_by(is_active=True).all()
        result = [{"uuid": c.uuid, "name": c.name, "description": c.description} for c in categories]
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return error_response(str(e), 500)

def get_products_action():
    try:
        # 🔥 1. Get Query Parameters from URL
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search_query = request.args.get('search', '').strip()
        category_uuid = request.args.get('category', '').strip()
        sort_by = request.args.get('sort_by', 'newest')

        # ==========================================
        # 🎩 THE MAGIC QUERY (Relational Integrity)
        # Ye sirf un products ko layega jo active hain 
        # AND jinka seller (User) bhi active hai.
        # ==========================================
        query = Product.query.join(User).filter(
            Product.is_active == True,
            User.is_active == True
        )

        # 🔥 2. Search Logic
        if search_query:
            query = query.filter(Product.name.ilike(f"%{search_query}%") | Product.description.ilike(f"%{search_query}%"))

        # 🔥 3. Category Filter
        if category_uuid:
            category = Category.query.filter_by(uuid=category_uuid, is_active=True).first()
            if category:
                # Jab JOIN use karte hain toh .filter() zyada safe hota hai .filter_by() se
                query = query.filter(Product.category_id == category.id)

        # 🔥 4. Sorting Logic
        if sort_by == 'price_low_to_high':
            query = query.order_by(Product.price.asc())
        elif sort_by == 'price_high_to_low':
            query = query.order_by(Product.price.desc())
        else: # default: newest
            query = query.order_by(Product.created_at.desc())

        # 🔥 5. Pagination Apply Karo
        paginated_products = query.paginate(page=page, per_page=limit, error_out=False)

        result = [serialize_seller_product(p) for p in paginated_products.items]

        return jsonify({
            "success": True, 
            "total_results": paginated_products.total,
            "total_pages": paginated_products.pages,
            "current_page": paginated_products.page,
            "data": result
        }), 200
    except Exception as e:
        return error_response(str(e), 500)

def get_single_product_action(product_uuid):
    try:
        # 🔥 MAGIC QUERY in Single Product
        # Taki blocked seller ka product direct link se bhi access na ho
        product = Product.query.join(User).filter(
            Product.uuid == product_uuid, 
            Product.is_active == True,
            User.is_active == True
        ).first()
        
        if not product:
            return error_response("Product not found or seller is inactive", 404)
        
        return jsonify({"success": True, "data": serialize_seller_product(product)}), 200
    except Exception as e:
        return error_response(str(e), 500)