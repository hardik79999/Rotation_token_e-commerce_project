from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User, Payment, Order, PaymentStatus, OrderStatus, CartItem, Product, OrderItem
from shop.utils.api_response import error_response
from shop.utils.razorpay_service import get_razorpay_client

def verify_payment_action():
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid, is_active=True).first()
        
        data = request.get_json() or {}
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        # 1. Fetch Payment & Security Check
        payment_record = Payment.query.filter_by(transaction_id=razorpay_order_id).first()
        if not payment_record or payment_record.user_id != user.id:
            return error_response("Payment record not found or unauthorized", 403)
        
        if payment_record.status == PaymentStatus.completed:
            return jsonify({"success": True, "message": "Already processed"}), 200

        # 2. Real Razorpay Signature Verification (NO BYPASS)
        client = get_razorpay_client()
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })

        # 3. ATOMIC STOCK DEDUCTION
        order = Order.query.get(payment_record.order_id)
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        
        for item in order_items:
            affected = Product.query.filter(Product.id == item.product_id, Product.stock >= item.quantity).update({"stock": Product.stock - item.quantity})
            if not affected:
                # In real industry, you'd trigger a refund here if stock ran out during payment window
                return error_response("Item went out of stock during payment!", 400)

        # 4. Success Updates
        payment_record.status = PaymentStatus.completed
        payment_record.gateway_payment_id = razorpay_payment_id # Store real payment ID
        order.status = OrderStatus.processing
        
        CartItem.query.filter_by(user_id=user.id, is_active=True).update({"is_active": False})
        
        db.session.commit()
        return jsonify({"success": True, "message": "Order confirmed and stock updated!"}), 200

    except Exception as e:
        db.session.rollback()
        return error_response("Signature verification failed", 400)