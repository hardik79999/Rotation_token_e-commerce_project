import razorpay
from flask import request, jsonify, current_app
from shop.extensions import db
from shop.models import Payment, Order, PaymentStatus, OrderStatus, Product, OrderItem

def razorpay_webhook_action():
    try:
        payload = request.get_data(as_text=True) 
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET')
        
        client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET']))
        client.utility.verify_webhook_signature(payload, webhook_signature, webhook_secret)

        data = request.get_json()
        if data.get('event') == 'payment.captured':
            payment_entity = data['payload']['payment']['entity']
            order_id_razorpay = payment_entity.get('order_id')
            
            payment_record = Payment.query.filter_by(transaction_id=order_id_razorpay).first()
            
            if payment_record and payment_record.status != PaymentStatus.completed:
                # Deduct Stock (Same logic as verify_payment)
                order = Order.query.get(payment_record.order_id)
                for item in order.items:
                    Product.query.filter(Product.id == item.product_id, Product.stock >= item.quantity).update({"stock": Product.stock - item.quantity})
                
                payment_record.status = PaymentStatus.completed
                order.status = OrderStatus.processing
                db.session.commit()

        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400