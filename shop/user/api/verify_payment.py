from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request
from shop.extensions import db
# 🔥 NAYA: PaymentStatus aur OrderStatus Enums import kiye
from shop.models import User, Payment, Order, PaymentStatus, OrderStatus, CartItem
from shop.utils.api_response import error_response
from shop.utils.razorpay_service import get_razorpay_client

# Purana import shayad aisa hoga:
from flask_jwt_extended import verify_jwt_in_request

# 🔥 Isko badal kar ye kar do:
from flask_jwt_extended import verify_jwt_in_request, get_jwt

from flask import current_app

def verify_payment_action():
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid).first()
        data = request.get_json() or {}

        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')

        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return error_response("Missing payment verification details", 400)

        # ==========================================
        # 🔥 POSTMAN HACK: GOOGLE RAZORPAY ABHI KE LIYE BYPASS
        # ==========================================
        if razorpay_signature == "postman_test_123":
            # Direct verification pass
            pass 
        else:
            # Asli Razorpay Verification (Jab live karna ho tab)
            client = get_razorpay_client()
            try:
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                })
            except Exception:
                return error_response("Invalid Signature.", 400)

        # ==========================================
        # 🎉 SUCCESS: DATABASE UPDATE KARO
        # ==========================================
        payment_record = Payment.query.filter_by(transaction_id=razorpay_order_id).first()
        
        if payment_record:
            payment_record.status = PaymentStatus.completed 
            payment_record.transaction_id = razorpay_payment_id 
            
            order_record = Order.query.get(payment_record.order_id)
            if order_record:
                order_record.status = OrderStatus.processing 
        
        # 🔥 CART EMPTY LOGIC (Hack mode mein bhi chalega)
        # Hum user ke active cart items ko deactivate kar rahe hain
        CartItem.query.filter_by(user_id=user.id, is_active=True).update({"is_active": False})
        
        db.session.commit() # Database me save karo

        return jsonify({
            "success": True, 
            "message": "Payment verified and Cart Emptied!"
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Payment Failed: {str(e)}")
        return error_response(str(e), 500)