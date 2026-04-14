from shop.admin import admin_bp
from shop.admin.api.create_category import create_category_action
from shop.admin.api.approve_category import approve_category_action
from shop.admin.api.manage_seller import toggle_seller_status_action
from shop.admin.api.dashboard import admin_dashboard_action

@admin_bp.route('/category', methods=['POST'])
def create_category_route():
    """
    Create New Category
    ---
    tags:
      - 🛡️ Admin Panel
    security:
      - CSRF-Token: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            name: {type: string}
            description: {type: string}
    responses:
      201:
        description: Category Created
    """
    return create_category_action()

@admin_bp.route('/approve-category/<seller_category_uuid>', methods=['PUT'])
def approve_seller_category_route(seller_category_uuid):
    """
    Approve/Reject Seller Category Request
    ---
    tags:
      - 🛡️ Admin Panel
    security:
      - CSRF-Token: []
    parameters:
      - name: seller_category_uuid
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          properties:
            action: {type: string, enum: ['approve', 'reject']}
    responses:
      200:
        description: Request processed
    """
    return approve_category_action(seller_category_uuid)

@admin_bp.route('/seller/<seller_uuid>/toggle-status', methods=['PUT'])
def toggle_seller_route(seller_uuid):
    """
    Block/Unblock Seller (Toggle Status)
    ---
    tags:
      - 🛡️ Admin Panel
    security:
      - CSRF-Token: []
    parameters:
      - name: seller_uuid
        in: path
        type: string
        required: true
    responses:
      200:
        description: Seller status updated
    """
    return toggle_seller_status_action(seller_uuid)





@admin_bp.route('/dashboard', methods=['GET'])
def admin_dashboard_route():
    """
    Admin Analytics Dashboard 📊
    ---
    tags:
      - 🛡️ Admin Panel
    security:
      - CSRF-Token: []
    responses:
      200:
        description: Dashboard stats
    """
    return admin_dashboard_action()