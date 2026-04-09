import json
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Category, Product, ProductImage, Specification, User
from shop.utils.api_response import error_response
from shop.utils.file_handler import save_image
from shop.seller.api.helpers import ensure_seller_category_access, serialize_seller_product

def update_product_action(product_uuid):
    try:
        verify_jwt_in_request()
        seller = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()

        product = Product.query.filter_by(uuid=product_uuid, seller_id=seller.id, is_active=True).first()
        if not product: return error_response('Product not found', 404)

        is_form_request = request.content_type and 'multipart/form-data' in request.content_type
        payload = request.form if is_form_request else (request.get_json() or {})

        name = (payload.get('name') or product.name).strip()
        description = (payload.get('description') or product.description).strip()
        price = payload.get('price', product.price)
        stock = payload.get('stock', product.stock)
        category_uuid = payload.get('category_uuid', product.category.uuid if product.category else None)
        specifications_data = payload.get('specifications')

        category = Category.query.filter_by(uuid=category_uuid, is_active=True).first()
        if not category: return error_response('Invalid category', 404)

        access_error = ensure_seller_category_access(seller.id, category.id, category.name)
        if access_error: return access_error

        product.name, product.description, product.price, product.stock, product.category_id, product.updated_by = name, description, float(price), int(stock), category.id, seller.id

        if specifications_data is not None:
            for spec in product.specifications:
                if spec.is_active: spec.is_active, spec.updated_by = False, seller.id
            parsed_specs = json.loads(specifications_data) if isinstance(specifications_data, str) else specifications_data
            for spec in parsed_specs or []:
                k, v = (spec.get('key') or '').strip(), (spec.get('value') or '').strip()
                if k and v: db.session.add(Specification(product_id=product.id, spec_key=k, spec_value=v, created_by=seller.id))

        image_files = request.files.getlist('images') if is_form_request else []
        if image_files and image_files[0].filename:
            for img in product.images:
                if img.is_active: img.is_active, img.is_primary, img.updated_by = False, False, seller.id
            for index, file in enumerate(image_files):
                img_url = save_image(file, folder_name="products")
                if img_url: db.session.add(ProductImage(product_id=product.id, image_url=img_url, is_primary=(index == 0), created_by=seller.id))

        db.session.commit()
        return jsonify({"success": True, "message": "Product updated", "data": serialize_seller_product(product)}), 200
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to update product', 500)