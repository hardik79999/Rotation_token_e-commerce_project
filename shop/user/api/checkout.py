from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
# 🔥 Dhyan do: Yahan 'Address' bhi import karna hai
from shop.models import User, Order, Payment, Address 
from shop.utils.api_response import error_response
from shop.utils.razorpay_service import get_razorpay_client
import uuid

from flask import request, jsonify, current_app

def checkout_action():
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid).first()

        data = request.get_json() or {}
        payment_method = data.get('payment_method', 'online') 
        address_uuid = data.get('address_uuid') # 🔥 NAYA: Address mangwao

        if not address_uuid:
            return error_response("Delivery address is required!", 400)

        # 🔥 NAYA: Database me address check karo
        delivery_address = Address.query.filter_by(uuid=address_uuid, user_id=user.id, is_active=True).first()
        if not delivery_address:
            return error_response("Invalid delivery address", 404)
        
        # 1. Cart ka Total Amount nikal lo (Abhi test ke liye 500 hai)
        total_amount = 500.00 

        # 2. Database me pending order banao (Ab address_id aur payment_method bhi daal diya)
        new_order = Order(
            user_id=user.id,
            address_id=delivery_address.id,   # 🔥 FIXED
            payment_method=payment_method,    # 🔥 FIXED
            total_amount=total_amount,
            status='pending',
            uuid=str(uuid.uuid4()),
            created_by=user.id
        )
        db.session.add(new_order)
        db.session.flush() # ID generate karne ke liye

        if payment_method == 'cod':
            new_order.status = 'confirmed'
            db.session.commit()
            return jsonify({"success": True, "message": "COD Order Placed!", "method": "cod"}), 201

        # ==========================================
        # 🔥 RAZORPAY ONLINE PAYMENT LOGIC
        # ==========================================
        client = get_razorpay_client()
        
        razorpay_order_data = {
            "amount": int(total_amount * 100), 
            "currency": "INR",
            "receipt": new_order.uuid,
            "payment_capture": 1 
        }
        
        razorpay_order = client.order.create(data=razorpay_order_data)

        # 3. Razorpay ki Order ID database me save karo
        new_payment = Payment(
            order_id=new_order.id,
            payment_method='razorpay',
            amount=total_amount,
            status='pending',
            transaction_id=razorpay_order['id'],
            created_by=user.id
        )
        db.session.add(new_payment)
        db.session.commit()

        return jsonify({
            "success": True,
            "method": "online",
            "data": {
                "razorpay_order_id": razorpay_order['id'],
                "amount": razorpay_order['amount'],
                "currency": razorpay_order['currency'],
                "key_id": current_app.config.get('RAZORPAY_KEY_ID')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print("CHECKOUT ERROR:", e)
        return error_response('Checkout failed', 500)