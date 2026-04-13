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
    """
    Create a New Product (With Multiple Images)
    ---
    tags:
      - 🏪 Seller Dashboard
    security:
      - CSRF-Token: []
    consumes:
      - multipart/form-data
    parameters:
      - name: name
        in: formData
        type: string
        required: true
      - name: description
        in: formData
        type: string
        required: true
      - name: price
        in: formData
        type: number
        required: true
      - name: stock
        in: formData
        type: integer
      - name: category_uuid
        in: formData
        type: string
        required: true
      - name: specifications
        in: formData
        type: string
      - name: images        # 🔥 YAHAN MULTIPLE ENABLE KIYA HAI
        in: formData
        type: array
        items:
          type: file
        collectionFormat: multi
        required: false
    responses:
      201:
        description: Product created successfully
    """
    return create_product_action()

@seller_bp.route('/products', methods=['GET'])
def get_products_route():
    """
    Get My Products (Seller)
    ---
    tags:
      - 🏪 Seller Dashboard
    security:
      - CSRF-Token: []
    responses:
      200:
        description: List of seller's products
    """
    return get_products_action()

@seller_bp.route('/product/<product_uuid>', methods=['PUT'])
def update_product_route(product_uuid):
    """
    Update Product (With Images)
    ---
    tags:
      - 🏪 Seller Dashboard
    security:
      - CSRF-Token: []
    consumes:
      - multipart/form-data
    parameters:
      - name: product_uuid
        in: path
        type: string
        required: true
      - name: name
        in: formData
        type: string
        required: false
      - name: description
        in: formData
        type: string
        required: false
      - name: price
        in: formData
        type: number
        required: false
      - name: stock
        in: formData
        type: integer
        required: false
      - name: category_uuid
        in: formData
        type: string
        required: false
      - name: specifications
        in: formData
        type: string
        required: false
      - name: images
        in: formData
        type: file
        required: false
    responses:
      200:
        description: Product updated
    """
    return update_product_action(product_uuid)

@seller_bp.route('/product/<product_uuid>', methods=['DELETE'])
def delete_product_route(product_uuid):
    """
    Delete Product (Soft Delete)
    ---
    tags:
      - 🏪 Seller Dashboard
    security:
      - CSRF-Token: []
    parameters:
      - name: product_uuid
        in: path
        type: string
        required: true
    responses:
      200:
        description: Product deleted
    """
    return delete_product_action(product_uuid)

@seller_bp.route('/category-request', methods=['POST'])
def category_request_route():
    """
    Request Category Approval
    ---
    tags:
      - 🏪 Seller Dashboard
    security:
      - CSRF-Token: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            category_uuid: {type: string}
    responses:
      201:
        description: Request sent to admin
    """
    return category_request_action()

@seller_bp.route('/my-categories', methods=['GET'])
def get_categories_route():
    """
    View Approved Categories
    ---
    tags:
      - 🏪 Seller Dashboard
    security:
      - CSRF-Token: []
    responses:
      200:
        description: List of approved categories
    """
    return get_categories_action()  

@seller_bp.route('/order/<order_uuid>/status', methods=['PUT'])
def update_order_status_route(order_uuid):
    """
    Update Order Status
    ---
    tags:
      - 🏪 Seller Dashboard
    security:
      - CSRF-Token: []
    parameters:
      - name: order_uuid
        in: path
        type: string
        required: true
      - name: body
        in: body
        required: true
        schema:
          properties:
            status: {type: string, enum: ['processing', 'shipped', 'delivered', 'cancelled']}
    responses:
      200:
        description: Status updated and email sent
    """
    return update_order_status_action(order_uuid)