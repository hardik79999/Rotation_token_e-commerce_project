from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.extensions import db
from shop.models import Order, OrderStatus, User
from shop.utils.api_response import error_response
from shop.utils.email_service import send_order_status_email

def update_order_status_action(order_uuid):
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        
        # 🔥 Role Check: Sirf Admin ya Seller isko badal sakte hain
        if claims.get("role") not in ["admin", "seller"]:
            return error_response("Unauthorized! Only Admins or Sellers can update orders.", 403)

        data = request.get_json()
        new_status_str = data.get("status", "").lower()

        try:
            new_status_enum = OrderStatus[new_status_str]
        except KeyError:
            return error_response(f"Invalid status. Use: {', '.join([e.name for e in OrderStatus])}", 400)

        order = Order.query.filter_by(uuid=order_uuid).first()
        if not order:
            return error_response("Order not found", 404)

        # Status Update karo
        order.status = new_status_enum
        db.session.commit()

        # 🔥 Customer ko email bhejo
        customer = User.query.get(order.user_id)
        if customer:
            send_order_status_email(customer.email, order.uuid, new_status_enum.name)
            current_app.logger.info(f"Order {order.uuid} updated to {new_status_enum.name}. Email sent to {customer.email}")

        return jsonify({"success": True, "message": f"Order status updated to {new_status_enum.name}"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Order Update Error: {str(e)}")
        return error_response(str(e), 500)