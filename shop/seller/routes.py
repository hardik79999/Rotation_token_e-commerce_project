from shop.seller import seller_bp

from shop.seller.api.create_product import create_product_action
from shop.seller.api.get_products import get_products_action
from shop.seller.api.update_product import update_product_action
from shop.seller.api.delete_product import delete_product_action
from shop.seller.api.category_request import category_request_action
from shop.seller.api.get_categories import get_categories_action
from shop.seller.api.order_status import update_order_status_action

@seller_bp.route('/product', methods=['POST'])
def create_product_route():
    return create_product_action()

@seller_bp.route('/products', methods=['GET'])
def get_products_route():
    return get_products_action()

@seller_bp.route('/product/<product_uuid>', methods=['PUT'])
def update_product_route(product_uuid):
    return update_product_action(product_uuid)

@seller_bp.route('/product/<product_uuid>', methods=['DELETE'])
def delete_product_route(product_uuid):
    return delete_product_action(product_uuid)

@seller_bp.route('/category-request', methods=['POST'])
def category_request_route():
    return category_request_action()

@seller_bp.route('/my-categories', methods=['GET'])
def get_categories_route():
    return get_categories_action()  

@seller_bp.route('/order/<order_uuid>/status', methods=['PUT'])
def update_order_status_route(order_uuid):
    return update_order_status_action(order_uuid)