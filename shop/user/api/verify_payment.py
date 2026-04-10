from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request
from shop.extensions import db
from shop.models import Payment, Order
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

        # 🔥 Yahan Razorpay verify karega ki ye signature valid hai ya hacker ne banaya hai
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
        except Exception as e:
            # Agar error aaya matlab payment fake hai ya fail ho gayi
            return error_response("Payment verification failed! Invalid Signature.", 400)

        # Agar code yahan tak aa gaya, matlab Payment 100% SUCCESS hai! 🎉
        payment_record = Payment.query.filter_by(transaction_id=razorpay_order_id).first()
        
        if payment_record:
            payment_record.status = 'success'
            payment_record.transaction_id = razorpay_payment_id # Order ID ki jagah ab Payment ID save kar lo future refunds ke liye
            
            order_record = Order.query.get(payment_record.order_id)
            if order_record:
                order_record.status = 'confirmed'

            db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Payment verified and Order confirmed successfully!"
        }), 200

    except Exception as e:
        db.session.rollback()
        print("PAYMENT VERIFY ERROR:", e)
        return error_response("Server error during verification", 500)