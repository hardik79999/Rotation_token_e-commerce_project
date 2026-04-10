from shop.models import ProductImage, Specification, SellerCategory
from shop.utils.api_response import error_response

def serialize_seller_product(product):
    # Primary image nikalo, agar nahi hai toh pehli active image ko primary maan lo
    primary_image = ProductImage.query.filter_by(product_id=product.id, is_primary=True, is_active=True).first()
    images = ProductImage.query.filter_by(product_id=product.id, is_active=True).order_by(ProductImage.created_at.asc()).all()
    
    if not primary_image and images:
        primary_image = images[0] # Fallback

    specifications = Specification.query.filter_by(product_id=product.id, is_active=True).order_by(Specification.created_at.asc()).all()

    return {
        'uuid': product.uuid,
        'name': product.name,
        'description': product.description,
        'price': float(product.price),
        'stock': product.stock,
        'category': product.category.name if product.category else "Unknown",
        'category_uuid': product.category.uuid if product.category else None,
        'primary_image': primary_image.image_url if primary_image else None,
        'images': [{"uuid": img.uuid, "url": img.image_url, "is_primary": img.is_primary} for img in images],
        'specifications': [{'key': spec.spec_key, 'value': spec.spec_value} for spec in specifications],
        'is_active': product.is_active
    }

def ensure_seller_category_access(seller_id, category_id, category_name):
    is_approved_seller = SellerCategory.query.filter_by(seller_id=seller_id, category_id=category_id, is_approved=True, is_active=True).first()
    if not is_approved_seller:
        return error_response(f"Category approval required for '{category_name}'. Please request admin approval first.", 403)
    return None