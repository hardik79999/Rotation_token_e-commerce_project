import uuid
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User, Order, Payment, Address, PaymentMethod, OrderStatus, CartItem, OrderItem, PaymentStatus
from shop.utils.api_response import error_response
from shop.utils.razorpay_service import get_razorpay_client

def checkout_action():
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid).first()

        data = request.get_json() or {}
        method_str = data.get('payment_method', 'cod').lower()
        address_uuid = data.get('address_uuid')

        if not address_uuid:
            return error_response("Delivery address is required!", 400)

        delivery_address = Address.query.filter_by(uuid=address_uuid, user_id=user.id, is_active=True).first()
        if not delivery_address:
            return error_response("Invalid delivery address", 404)

        try:
            selected_method = PaymentMethod[method_str]
        except KeyError:
            return error_response(f"Invalid payment method. Use: {', '.join([e.name for e in PaymentMethod])}", 400)
        
        cart_items = CartItem.query.filter_by(user_id=user.id, is_active=True).all()
        if not cart_items:
            return error_response("Your cart is empty!", 400)

        total_amount = sum(item.quantity * item.product.price for item in cart_items)

        # 1. Create Order
        new_order = Order(
            user_id=user.id,
            address_id=delivery_address.id,
            payment_method=selected_method,
            total_amount=total_amount,
            status=OrderStatus.pending,
            uuid=str(uuid.uuid4()),
            created_by=user.id
        )
        db.session.add(new_order)
        db.session.flush() # ID generate karne ke liye

        # 2. 🔥 Fix: Copy Cart to Order Items
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product.id,
                quantity=item.quantity,
                price_at_purchase=item.product.price,
                created_by=user.id
            )
            db.session.add(order_item)
            item.is_active = False # Soft delete cart

        # 3. Handle COD vs Online
        if selected_method == PaymentMethod.cod:
            new_order.status = OrderStatus.processing
            
            # 🔥 Fix: COD Payment Entry
            db.session.add(Payment(
                order_id=new_order.id,
                user_id=user.id,
                payment_method=PaymentMethod.cod,
                amount=total_amount,
                status=PaymentStatus.pending,
                transaction_id=f"COD-{new_order.uuid[:8].upper()}",
                created_by=user.id
            ))
            db.session.commit()
            return jsonify({"success": True, "message": "COD Order Placed!", "order_uuid": new_order.uuid}), 201

        # Online Flow (UPI/Card)
        client = get_razorpay_client()
        razorpay_order = client.order.create({
            "amount": int(total_amount * 100), 
            "currency": "INR",
            "receipt": new_order.uuid,
            "payment_capture": 1 
        })

        db.session.add(Payment(
            order_id=new_order.id,
            user_id=user.id,
            payment_method=selected_method,
            amount=total_amount,
            status=PaymentStatus.pending,
            transaction_id=razorpay_order['id'],
            created_by=user.id
        ))
        db.session.commit()

        return jsonify({"success": True, "data": {"razorpay_order_id": razorpay_order['id'], "amount": total_amount}}), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f"Checkout failed: {str(e)}", 500)