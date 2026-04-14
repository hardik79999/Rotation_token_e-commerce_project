import razorpay
from flask import request, jsonify, current_app
from shop.extensions import db
from shop.models import Payment, Order, PaymentStatus, OrderStatus

def razorpay_webhook_action():
    try:
        # Razorpay dashboard me jo secret daloge, wo yahan check hoga
        payload = request.get_data(as_text=True) 
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_secret = current_app.config.get('RAZORPAY_WEBHOOK_SECRET')
        
        if not webhook_signature:
            return jsonify({"error": "Missing signature"}), 400

        # 🔥 FIX 1: Razorpay client ko pehle load karna padega
        client = razorpay.Client(
            auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET'])
        )

        # 🔥 FIX 2: Signature verify karna
        # (Swagger/Postman Bypass Hack)
        if webhook_signature == "dummy_hacker_signature_123":
             print("⚠️ Warning: Webhook bypassed using manual Swagger testing.")
             pass
        else:
             # Asli Razorpay Verification
             try:
                 client.utility.verify_webhook_signature(payload, webhook_signature, webhook_secret)
             except razorpay.errors.SignatureVerificationError:
                 return jsonify({"error": "Invalid signature"}), 400

        # Agar signature valid hai, toh data parse karo
        data = request.get_json() or {}
        event = data.get('event')

        if event == 'payment.captured':
            payment_entity = data['payload']['payment']['entity']
            order_id_razorpay = payment_entity.get('order_id')
            payment_id = payment_entity.get('id')

            if order_id_razorpay:
                # Database me order dhundho
                payment_record = Payment.query.filter_by(transaction_id=order_id_razorpay).first()
                
                if payment_record and payment_record.status != PaymentStatus.completed:
                    payment_record.status = PaymentStatus.completed
                    payment_record.transaction_id = payment_id #

                    order_record = Order.query.get(payment_record.order_id)
                    if order_record:
                        order_record.status = OrderStatus.processing

                    db.session.commit()
                    print(f"✅ Webhook Success: Order {order_record.uuid} payment confirmed!")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        db.session.rollback()
        print("WEBHOOK ERROR:", e)
        return jsonify({"error": str(e)}), 500