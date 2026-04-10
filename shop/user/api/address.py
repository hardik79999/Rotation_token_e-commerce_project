import uuid
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User, Address
from shop.utils.api_response import error_response

def add_address_action():
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid).first()

        data = request.get_json() or {}
        
        # Validation
        required = ['full_name', 'phone_number', 'street', 'city', 'state', 'pincode']
        if not all(k in data for k in required):
            return error_response("All address fields are required", 400)

        # Naya Address Object
        new_address = Address(
            uuid=str(uuid.uuid4()), # 🔥 Frontend ke liye UUID generate kiya
            user_id=user.id,
            full_name=data['full_name'],
            phone_number=data['phone_number'],
            street=data['street'],
            city=data['city'],
            state=data['state'],
            pincode=data['pincode'],
            is_default=data.get('is_default', False),
            created_by=user.id
        )

        db.session.add(new_address)
        db.session.commit() # 🔥 Database me save ho gaya

        return jsonify({
            "success": True,
            "message": "Address saved successfully!",
            "data": {
                "uuid": new_address.uuid, # 🔥 Ye jayega frontend ko
                "city": new_address.city
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)

def get_addresses_action():
    try:
        verify_jwt_in_request()
        user = User.query.filter_by(uuid=get_jwt().get("user_uuid")).first()

        addresses = Address.query.filter_by(user_id=user.id, is_active=True).all()
        
        result = []
        for a in addresses:
            result.append({
                "uuid": a.uuid, # 🔥 Frontend iska use checkout me karega
                "full_name": a.full_name,
                "address_line": f"{a.street}, {a.city}, {a.state} - {a.pincode}",
                "phone": a.phone_number
            })

        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return error_response(str(e), 500)