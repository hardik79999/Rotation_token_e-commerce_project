import json
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Category, Product, ProductImage, Role, SellerCategory, Specification, User
from shop.seller import seller_bp
from shop.utils.api_response import error_response, success_response
from shop.utils.file_handler import save_image

# (Agar tumhare email_service me ye function nahi hai, toh add kar lena warna is line ko error aaye toh hata dena)
from shop.utils.email_service import send_category_request_email_to_admin 


# =====================================================================
# HELPER: Serialize Product
# =====================================================================
def serialize_seller_product(product):
    primary_image = ProductImage.query.filter_by(
        product_id=product.id,
        is_primary=True,
        is_active=True,
    ).first()

    images = ProductImage.query.filter_by(
        product_id=product.id,
        is_active=True,
    ).order_by(ProductImage.created_at.asc()).all()

    specifications = Specification.query.filter_by(
        product_id=product.id,
        is_active=True,
    ).order_by(Specification.created_at.asc()).all()

    return {
        'uuid': product.uuid,
        'name': product.name,
        'description': product.description,
        'price': float(product.price),
        'stock': product.stock,
        'category': product.category.name,
        'category_uuid': product.category.uuid,
        'primary_image': primary_image.image_url if primary_image else None,
        'images': [image.image_url for image in images],
        'specifications': [{'key': spec.spec_key, 'value': spec.spec_value} for spec in specifications],
        'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else None,
        'updated_at': product.updated_at.strftime('%Y-%m-%d %H:%M:%S') if product.updated_at else None,
    }

# =====================================================================
# HELPER: Check Category Access
# =====================================================================
def ensure_seller_category_access(seller_id, category_id, category_name):
    is_approved_seller = SellerCategory.query.filter_by(
        seller_id=seller_id,
        category_id=category_id,
        is_approved=True,
        is_active=True,
    ).first()

    if not is_approved_seller:
        return error_response(
            f"Category approval required for '{category_name}'. Please request admin approval first.",
            403
        )
    return None

# =====================================================================
# 1. CREATE PRODUCT (POST) - With Images & Specifications
# =====================================================================
@seller_bp.route('/product', methods=['POST'])
def create_product():
    try:
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("role") != "seller":
            return error_response("Unauthorized! Only sellers can add products.", 403)

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

        # Access check
        access_error = ensure_seller_category_access(seller.id, category.id, category.name)
        if access_error:
            return access_error

        # Handle Images using generic save_image function
        image_files = request.files.getlist('images')
        saved_image_urls = []

        if image_files and image_files[0].filename != '':
            for file in image_files:
                image_url = save_image(file, folder_name="products")
                if image_url:
                    saved_image_urls.append(image_url)

        # Create Product
        new_product = Product(
            name=name,
            description=description,
            price=float(price),
            stock=int(stock),
            category_id=category.id,
            seller_id=seller.id,
            created_by=seller.id
        )
        db.session.add(new_product)
        db.session.flush() # ID generation ke liye

        # Save Image Records
        for index, url in enumerate(saved_image_urls):
            db.session.add(ProductImage(
                product_id=new_product.id,
                image_url=url,
                is_primary=(index == 0),
                created_by=seller.id
            ))

        # Parse and Save Specifications
        parsed_specs = []
        if specifications_data:
            try:
                spec_list = json.loads(specifications_data)
                for spec in spec_list:
                    spec_key = (spec.get('key') or '').strip()
                    spec_value = (spec.get('value') or '').strip()
                    if spec_key and spec_value:
                        db.session.add(Specification(
                            product_id=new_product.id,
                            spec_key=spec_key,
                            spec_value=spec_value,
                            created_by=seller.id
                        ))
                        parsed_specs.append({'key': spec_key, 'value': spec_value})
            except json.JSONDecodeError:
                db.session.rollback()
                return error_response('Invalid format for specifications. It must be a valid JSON array.', 400)

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Product created successfully with images and specs",
            "data": {
                "uuid": new_product.uuid,
                "name": new_product.name,
                "price": float(new_product.price),
                "images": saved_image_urls,
                "specifications": parsed_specs
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print("CREATE PRODUCT ERROR:", e)
        return error_response('Failed to create product', 500)


# =====================================================================
# 2. GET MY PRODUCTS (GET)
# =====================================================================
@seller_bp.route('/products', methods=['GET'])
def get_my_products():
    try:
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("role") != "seller":
            return error_response("Unauthorized!", 403)

        seller = User.query.filter_by(uuid=claims.get("user_uuid")).first()

        products = Product.query.filter_by(
            seller_id=seller.id,
            is_active=True,
        ).order_by(Product.created_at.desc()).all()

        result = [serialize_seller_product(product) for product in products]
        
        return jsonify({
            "success": True,
            "message": "Seller products loaded successfully.",
            "total_products": len(result),
            "data": result
        }), 200

    except Exception as e:
        print("GET PRODUCTS ERROR:", e)
        return error_response(str(e), 500)


# =====================================================================
# 3. UPDATE PRODUCT (PUT)
# =====================================================================
@seller_bp.route('/product/<product_uuid>', methods=['PUT'])
def update_product(product_uuid):
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        seller = User.query.filter_by(uuid=claims.get("user_uuid")).first()

        product = Product.query.filter_by(
            uuid=product_uuid,
            seller_id=seller.id,
            is_active=True,
        ).first()
        
        if not product:
            return error_response('Product not found', 404)

        is_form_request = request.content_type and 'multipart/form-data' in request.content_type
        payload = request.form if is_form_request else (request.get_json() or {})

        name = (payload.get('name') or product.name).strip()
        description = (payload.get('description') or product.description).strip()
        price = payload.get('price', product.price)
        stock = payload.get('stock', product.stock)
        category_uuid = payload.get('category_uuid', product.category.uuid if product.category else None)
        specifications_data = payload.get('specifications')

        category = Category.query.filter_by(uuid=category_uuid, is_active=True).first()
        if not category:
            return error_response('Invalid or inactive category', 404)

        access_error = ensure_seller_category_access(seller.id, category.id, category.name)
        if access_error:
            return access_error

        image_files = request.files.getlist('images') if is_form_request else []
        has_new_images = bool(image_files and image_files[0].filename)

        # Update Product
        product.name = name
        product.description = description
        product.price = float(price)
        product.stock = int(stock)
        product.category_id = category.id
        product.updated_by = seller.id

        # Update Specifications
        if specifications_data is not None:
            # Soft delete old specs
            for existing_spec in product.specifications:
                if existing_spec.is_active:
                    existing_spec.is_active = False
                    existing_spec.updated_by = seller.id

            parsed_specs = json.loads(specifications_data) if isinstance(specifications_data, str) else specifications_data
            for spec in parsed_specs or []:
                spec_key = (spec.get('key') or '').strip()
                spec_value = (spec.get('value') or '').strip()
                if spec_key and spec_value:
                    db.session.add(Specification(
                        product_id=product.id,
                        spec_key=spec_key,
                        spec_value=spec_value,
                        created_by=seller.id,
                        updated_by=seller.id
                    ))

        # Update Images
        if has_new_images:
            # Soft delete old images
            for existing_image in product.images:
                if existing_image.is_active:
                    existing_image.is_active = False
                    existing_image.is_primary = False
                    existing_image.updated_by = seller.id

            # Save new images
            for index, file in enumerate(image_files):
                image_url = save_image(file, folder_name="products")
                if image_url:
                    db.session.add(ProductImage(
                        product_id=product.id,
                        image_url=image_url,
                        is_primary=(index == 0),
                        created_by=seller.id,
                        updated_by=seller.id
                    ))

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Product updated successfully",
            "data": serialize_seller_product(product)
        }), 200

    except Exception as e:
        db.session.rollback()
        print("UPDATE PRODUCT ERROR:", e)
        return error_response('Failed to update product', 500)


# =====================================================================
# 4. DELETE PRODUCT (DELETE)
# =====================================================================
@seller_bp.route('/product/<product_uuid>', methods=['DELETE'])
def delete_product(product_uuid):
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        seller = User.query.filter_by(uuid=claims.get("user_uuid")).first()

        product = Product.query.filter_by(
            uuid=product_uuid,
            seller_id=seller.id,
            is_active=True,
        ).first()

        if not product:
            return error_response('Product not found', 404)

        product.is_active = False
        product.updated_by = seller.id

        for image in product.images:
            image.is_active = False
            image.updated_by = seller.id

        for specification in product.specifications:
            specification.is_active = False
            specification.updated_by = seller.id

        db.session.commit()
        return success_response(f"Product '{product.name}' deleted successfully.")

    except Exception as e:
        db.session.rollback()
        print("DELETE PRODUCT ERROR:", e)
        return error_response('Failed to delete product', 500)


# =====================================================================
# 5. REQUEST CATEGORY APPROVAL (POST)
# =====================================================================
@seller_bp.route('/category-request', methods=['POST'])
def request_category_approval():
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        seller = User.query.filter_by(uuid=claims.get("user_uuid")).first()

        data = request.get_json() or {}
        category_uuid = (data.get('category_uuid') or '').strip()
        
        if not category_uuid:
            return error_response('category_uuid is required', 400)

        category = Category.query.filter_by(uuid=category_uuid, is_active=True).first()
        if not category:
            return error_response('Category not found or inactive', 404)

        existing_request = SellerCategory.query.filter_by(
            seller_id=seller.id,
            category_id=category.id,
            is_active=True,
        ).first()

        if existing_request:
            status = 'Approved' if existing_request.is_approved else 'Pending'
            return error_response(f'You already have a {status} request for this category. Please wait for admin approval.', 400)

        new_request = SellerCategory(
            seller_id=seller.id,
            category_id=category.id,
            is_approved=False,
            created_by=seller.id
        )
        db.session.add(new_request)
        db.session.commit()

        email_sent = False
        try:
            admin_role = Role.query.filter_by(role_name='admin').first()
            active_admins = User.query.filter_by(role_id=admin_role.id, is_active=True).all() if admin_role else []
            if active_admins:
                admin_emails = [admin.email for admin in active_admins if admin.email]
                if admin_emails:
                    email_sent = send_category_request_email_to_admin(
                        admin_emails=admin_emails,
                        seller_name=seller.username,
                        category_name=category.name,
                    )
        except Exception as exc:
            print('Admin email sending failed:', exc)

        return jsonify({
            "success": True,
            "message": f"Request to sell in '{category.name}' submitted successfully.",
            "data": {
                "request_uuid": new_request.uuid,
                "email_status": 'Admin notification email sent successfully.' if email_sent else 'Request saved, but admin email notification could not be sent.'
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print("CATEGORY REQUEST ERROR:", e)
        return error_response('Failed to submit request', 500)


# =====================================================================
# 6. GET MY CATEGORIES (GET)
# =====================================================================
@seller_bp.route('/my-categories', methods=['GET'])
def get_my_categories():
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        seller = User.query.filter_by(uuid=claims.get("user_uuid")).first()

        all_categories = Category.query.filter_by(is_active=True).all()
        seller_categories = SellerCategory.query.filter_by(
            seller_id=seller.id,
            is_active=True,
        ).all()

        seller_category_map = {
            sc.category_id: {
                'is_approved': sc.is_approved,
                'request_uuid': sc.uuid,
            }
            for sc in seller_categories
        }

        result = []
        for category in all_categories:
            category_data = {
                'uuid': category.uuid,
                'name': category.name,
                'description': category.description,
            }

            if category.id in seller_category_map:
                status_info = seller_category_map[category.id]
                category_data['status'] = 'approved' if status_info['is_approved'] else 'pending'
                category_data['request_uuid'] = status_info['request_uuid']
            else:
                category_data['status'] = 'available'

            result.append(category_data)

        return jsonify({
            "success": True,
            "message": "Seller categories loaded successfully.",
            "total_categories": len(result),
            "data": result
        }), 200

    except Exception as e:
        print("GET MY CATEGORIES ERROR:", e)
        return error_response(str(e), 500)