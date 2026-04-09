from shop.admin import admin_bp
from shop.admin.api.create_category import create_category_action
from shop.admin.api.approve_category import approve_category_action

@admin_bp.route('/category', methods=['POST'])
def create_category_route():
    return create_category_action()

@admin_bp.route('/approve-category/<seller_category_uuid>', methods=['PUT'])
def approve_seller_category_route(seller_category_uuid):
    return approve_category_action(seller_category_uuid)