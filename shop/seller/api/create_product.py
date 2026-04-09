import json
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Category, Product, ProductImage, Specification, User
from shop.utils.api_response import error_response
from shop.utils.file_handler import save_image
from shop.seller.api.helpers import ensure_seller_category_access

def create_product_action():
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "seller":
            return error_response("Unauthorized!", 403)

        seller = User.query.filter_by(uuid=claims.get("user_uuid")).first()

        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        price = request.form.get('price')
        stock = request.form.get('stock', 0)
        category_uuid = (request.form.get('category_uuid') or '').strip()
        specifications_data = request.form.get('specifications')

        if not all([name, description, price, category_uuid]):
            return error_response('Missing required text fields', 400)

        category = Category.query.filter_by(uuid=category_uuid, is_active=True).first()
        if not category:
            return error_response('Invalid or inactive category', 404)

        access_error = ensure_seller_category_access(seller.id, category.id, category.name)
        if access_error: return access_error

        image_files = request.files.getlist('images')
        saved_image_urls = []
        if image_files and image_files[0].filename != '':
            for file in image_files:
                img_url = save_image(file, folder_name="products")
                if img_url: saved_image_urls.append(img_url)

        new_product = Product(name=name, description=description, price=float(price), stock=int(stock), category_id=category.id, seller_id=seller.id, created_by=seller.id)
        db.session.add(new_product)
        db.session.flush() 

        for index, url in enumerate(saved_image_urls):
            db.session.add(ProductImage(product_id=new_product.id, image_url=url, is_primary=(index == 0), created_by=seller.id))

        parsed_specs = []
        if specifications_data:
            try:
                for spec in json.loads(specifications_data):
                    k, v = (spec.get('key') or '').strip(), (spec.get('value') or '').strip()
                    if k and v:
                        db.session.add(Specification(product_id=new_product.id, spec_key=k, spec_value=v, created_by=seller.id))
                        parsed_specs.append({'key': k, 'value': v})
            except json.JSONDecodeError:
                db.session.rollback()
                return error_response('Invalid JSON array for specifications.', 400)

        db.session.commit()
        return jsonify({"success": True, "message": "Product created successfully", "data": {"uuid": new_product.uuid, "name": new_product.name}}), 201
    except Exception as e:
        db.session.rollback()
        print("CREATE PRODUCT ERROR:", e)
        return error_response('Failed to create product', 500)