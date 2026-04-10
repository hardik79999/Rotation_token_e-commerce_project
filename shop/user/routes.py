from shop.user import user_bp

# Import APIs
from shop.user.api.browse import get_categories_action, get_products_action, get_single_product_action
from shop.user.api.address import add_address_action, get_addresses_action
from shop.user.api.cart import add_to_cart_action, get_cart_action, update_cart_item_action
from shop.user.api.wishlist import toggle_wishlist_action, get_wishlist_action
from shop.user.api.review import add_review_action
from shop.user.api.checkout import checkout_action
from shop.user.api.verify_payment import verify_payment_action
from shop.user.api.orders import get_orders_action
from shop.user.api.orders import get_orders_action, get_order_status_action


# ==========================================
# 🌐 PUBLIC BROWSING ROUTES (No Login Required)
# ==========================================
@user_bp.route('/categories', methods=['GET'])
def get_categories_route():
    return get_categories_action()

@user_bp.route('/products', methods=['GET'])
def get_products_route():
    return get_products_action()

@user_bp.route('/product/<product_uuid>', methods=['GET'])
def get_single_product_route(product_uuid):
    return get_single_product_action(product_uuid)

# ==========================================
# 📍 ADDRESS ROUTES (Requires Login)
# ==========================================
@user_bp.route('/address', methods=['POST'])
def add_address_route():
    return add_address_action()

@user_bp.route('/addresses', methods=['GET'])
def get_addresses_route():
    return get_addresses_action()

# ==========================================
# 🛒 CART ROUTES (Requires Login)
# ==========================================
@user_bp.route('/cart', methods=['POST'])
def add_to_cart_route():
    return add_to_cart_action()

@user_bp.route('/cart', methods=['GET'])
def get_cart_route():
    return get_cart_action()

@user_bp.route('/cart', methods=['PUT'])
def update_cart_route():
    return update_cart_item_action()

# ==========================================
# ❤️ WISHLIST & ⭐ REVIEW
# ==========================================
@user_bp.route('/wishlist', methods=['POST'])
def toggle_wishlist_route(): 
    return toggle_wishlist_action()

@user_bp.route('/wishlist', methods=['GET'])
def get_wishlist_route(): 
    return get_wishlist_action()

@user_bp.route('/review', methods=['POST'])
def add_review_route(): 
    return add_review_action()

# ==========================================
# 💸 CHECKOUT & ORDERS (PAYMENT FLOW)
# ==========================================
@user_bp.route('/checkout', methods=['POST'])
def checkout_route():
    return checkout_action()

@user_bp.route('/verify-payment', methods=['POST'])
def verify_payment_route():
    return verify_payment_action()

@user_bp.route('/orders', methods=['GET'])
def get_orders_route():
    return get_orders_action()

# 🔥 NAYA ROUTE: ORDER STATUS
@user_bp.route('/order/status/<order_uuid>', methods=['GET'])
def get_order_status_route(order_uuid):
    return get_order_status_action(order_uuid)