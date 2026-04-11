from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Category, SellerCategory, Role, User
from shop.utils.api_response import error_response
from shop.utils.email_service import send_category_request_email_to_admin

def category_request_action():
    try:
        verify_jwt_in_request()
        seller = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()
        data = request.get_json() or {}
        category_uuid = (data.get('category_uuid') or '').strip()
        
        if not category_uuid: return error_response('category_uuid required', 400)
        category = Category.query.filter_by(uuid=category_uuid, is_active=True).first()
        if not category: return error_response('Category not found', 404)

        existing = SellerCategory.query.filter_by(seller_id=seller.id, category_id=category.id, is_active=True).first()
        if existing:
            status = 'Approved' if existing.is_approved else 'Pending'
            return error_response(f'You already have a {status} request.', 400)

        # 🔥 YAHAN FIX KIYA HAI: is_active=True explicitly add kar diya taaki DB me humesha 1 jaye
        new_request = SellerCategory(
            seller_id=seller.id, 
            category_id=category.id, 
            is_approved=False, 
            is_active=True,  # <-- Ye sabse zaroori line
            created_by=seller.id
        )
        db.session.add(new_request)
        db.session.commit()

        email_sent = False
        try:
            admin_role = Role.query.filter_by(role_name='admin').first()
            active_admins = User.query.filter_by(role_id=admin_role.id, is_active=True).all() if admin_role else []
            if active_admins:
                admin_emails = [a.email for a in active_admins if a.email]
                if admin_emails: email_sent = send_category_request_email_to_admin(admin_emails, seller.username, category.name)
        except Exception: pass

        return jsonify({"success": True, "message": f"Request submitted.", "data": {"request_uuid": new_request.uuid, "email_status": email_sent}}), 201
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to submit request', 500)