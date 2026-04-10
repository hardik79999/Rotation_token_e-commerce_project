from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request
from shop.extensions import db
# 🔥 NAYA: PaymentStatus aur OrderStatus Enums import kiye
from shop.models import Payment, Order, PaymentStatus, OrderStatus 
from shop.utils.api_response import error_response
from shop.utils.razorpay_service import get_razorpay_client

def verify_payment_action():
    try:
        verify_jwt_in_request()
        data = request.get_json() or {}

        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')

        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return error_response("Missing payment verification details", 400)

        client = get_razorpay_client()

        # ==========================================
        # 🔥 POSTMAN HACK FOR LOCAL TESTING
        # ==========================================
        if razorpay_signature == "postman_test_123":
            pass # Hack: Postman me ye dalne se verify pass ho jayega
        else:
            # Asli Razorpay Verification
            try:
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                })
            except Exception as e:
                return error_response("Payment verification failed! Invalid Signature.", 400)

        # ==========================================
        # 🎉 SUCCESS: UPDATE DATABASE WITH ENUMS
        # ==========================================
        payment_record = Payment.query.filter_by(transaction_id=razorpay_order_id).first()
        
        if payment_record:
            payment_record.status = PaymentStatus.completed # 🔥 FIXED: Normal string ki jagah Enum
            payment_record.transaction_id = razorpay_payment_id 
            
            order_record = Order.query.get(payment_record.order_id)
            if order_record:
                order_record.status = OrderStatus.processing # 🔥 FIXED: Normal string ki jagah Enum

            db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Payment verified and Order confirmed successfully!"
        }), 200

    except Exception as e:
        db.session.rollback()
        print("PAYMENT VERIFY ERROR:", e)
        return error_response("Server error during verification", 500)