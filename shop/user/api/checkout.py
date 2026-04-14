import uuid
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import User, Order, Payment, Address, PaymentMethod, OrderStatus, CartItem, OrderItem, PaymentStatus, Product
from shop.utils.api_response import error_response
from shop.utils.razorpay_service import get_razorpay_client

def checkout_action():
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid, is_active=True).first()
        if not user: return error_response("User blocked or not found", 403)

        data = request.get_json() or {}
        method_str = data.get('payment_method', 'cod').lower()
        address_uuid = data.get('address_uuid')

        delivery_address = Address.query.filter_by(uuid=address_uuid, user_id=user.id, is_active=True).first()
        if not delivery_address: return error_response("Invalid delivery address", 404)

        try:
            selected_method = PaymentMethod[method_str]
        except KeyError: return error_response("Invalid payment method", 400)
        
        cart_items = CartItem.query.filter_by(user_id=user.id, is_active=True).all()
        if not cart_items: return error_response("Cart is empty!", 400)

        total_amount = 0
        order_items_to_add = []

        # 1. Validation & Atomic Stock Check (Pre-check)
        for item in cart_items:
            product = Product.query.with_for_update().get(item.product_id) # Row Lock
            if not product or not product.is_active or product.stock < item.quantity:
                return error_response(f"Product {product.name} is out of stock!", 400)
            
            total_amount += item.quantity * product.price
            order_items_to_add.append(OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                price_at_purchase=product.price,
                created_by=user.id
            ))

        # 2. Create Order
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
        db.session.flush()

        for oi in order_items_to_add:
            oi.order_id = new_order.id
            db.session.add(oi)

        # 3. Handle COD vs Online
        if selected_method == PaymentMethod.cod:
            # ATOMIC STOCK DEDUCTION for COD
            for item in cart_items:
                affected = Product.query.filter(Product.id == item.product_id, Product.stock >= item.quantity).update({"stock": Product.stock - item.quantity})
                if not affected:
                    db.session.rollback()
                    return error_response("Inventory sync error. Try again.", 500)
            
            new_order.status = OrderStatus.processing
            db.session.add(Payment(order_id=new_order.id, user_id=user.id, payment_method=PaymentMethod.cod, amount=total_amount, status=PaymentStatus.pending, transaction_id=f"COD-{new_order.uuid[:8].upper()}", created_by=user.id))
            
            CartItem.query.filter_by(user_id=user.id, is_active=True).update({"is_active": False}) # Clear Cart
            db.session.commit()
            return jsonify({"success": True, "order_uuid": new_order.uuid}), 201

        # Online Flow: Don't deduct stock yet, just create Razorpay order
        client = get_razorpay_client()
        razorpay_order = client.order.create({"amount": int(total_amount * 100), "currency": "INR", "receipt": new_order.uuid})

        db.session.add(Payment(order_id=new_order.id, user_id=user.id, payment_method=selected_method, amount=total_amount, status=PaymentStatus.pending, transaction_id=razorpay_order['id'], created_by=user.id))
        db.session.commit()

        return jsonify({"success": True, "data": {"razorpay_order_id": razorpay_order['id'], "amount": total_amount}}), 201

    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)