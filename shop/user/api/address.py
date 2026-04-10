from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User # Agar Address model hai toh yahan import karna (e.g., Address)
from shop.utils.api_response import error_response

# (Assuming tumhare paas Address model hai jisme fields hain: full_name, street, city, state, pincode)

def add_address_action():
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid).first()

        data = request.get_json() or {}
        # Basic validation
        if not all([data.get('full_name'), data.get('street'), data.get('city'), data.get('pincode')]):
            return error_response("Missing required address fields", 400)

        # HINT: Yahan apna Address model save karna
        # new_address = Address(user_id=user.id, full_name=data['full_name'], ...)
        # db.session.add(new_address)
        # db.session.commit()

        return jsonify({"success": True, "message": "Address added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to add address', 500)

def get_addresses_action():
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid).first()

        # HINT: user ke addresses fetch karna
        # addresses = Address.query.filter_by(user_id=user.id, is_active=True).all()
        # result = [{"uuid": a.uuid, "city": a.city, ...} for a in addresses]

        result = [] # Dummy data jab tak model na ban jaye
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return error_response(str(e), 500)