from flask import jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from shop.models import Order, Payment, User
from shop.utils.api_response import error_response

def generate_invoice_action(order_uuid):
    try:
        verify_jwt_in_request()
        user_uuid = get_jwt().get("user_uuid")
        user = User.query.filter_by(uuid=user_uuid).first()

        order = Order.query.filter_by(uuid=order_uuid, user_id=user.id).first()
        if not order:
            return error_response("Order not found or unauthorized", 404)

        payment = Payment.query.filter_by(order_id=order.id).first()

        # 🔥 FAKE TAX CALCULATION (Industry Standard: 18% GST Example)
        total_amount = float(order.total_amount)
        base_price = round(total_amount / 1.18, 2)
        tax_amount = round(total_amount - base_price, 2)

        # Invoice ka JSON structure
        invoice_data = {
            "invoice_id": f"INV-{order.id}-{order.created_at.strftime('%Y%m%d')}",
            "date": order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "status": order.status.name.upper(),
            "customer_details": {
                "name": user.username,
                "email": user.email,
                "phone": user.phone or "N/A",
                "shipping_address": order.shipping_address # Assuming ye field Order me hai
            },
            "payment_details": {
                "method": payment.payment_method if payment else "N/A",
                "transaction_id": payment.transaction_id if payment else "Pending",
                "payment_status": payment.status.name if payment else "Pending"
            },
            "order_summary": {
                # Yahan tum order items ka loop laga sakte ho agar OrderItem relation hai
                "base_amount": base_price,
                "tax_gst_18": tax_amount,
                "shipping_fee": 0.00, # Free shipping
                "grand_total": total_amount
            },
            "company_info": {
                "name": "Hardik E-Commerce Pvt. Ltd.",
                "support_email": "support@hardikstore.com",
                "gstin": "22AAAAA0000A1Z5"
            }
        }

        return jsonify({
            "success": True,
            "message": "Invoice generated successfully",
            "invoice": invoice_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"Invoice Generation Error: {str(e)}")
        return error_response("Failed to generate invoice", 500)