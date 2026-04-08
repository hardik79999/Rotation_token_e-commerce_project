import uuid
import enum
from datetime import datetime, timedelta
from shop.extensions import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Index, UniqueConstraint, CheckConstraint

# =================================================================================
# 🔁 BASE MODEL (DRY FIX)
# =================================================================================

class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    is_active = db.Column(db.Boolean, default=True, index=True)

    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now(), index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=db.func.now())


# =================================================================================
# ENUMS
# =================================================================================

class OrderStatus(enum.Enum):
    pending = 'pending'
    processing = 'processing'
    shipped = 'shipped'
    delivered = 'delivered'
    cancelled = 'cancelled'

class PaymentStatus(enum.Enum):
    pending = 'pending'
    completed = 'completed'
    failed = 'failed'
    refunded = 'refunded'

class PaymentMethod(enum.Enum):
    cod = 'cod'
    card = 'card'
    upi = 'upi'
    netbanking = 'netbanking'

class OTPAction(enum.Enum):
    verification = 'verification'
    password_reset = 'password_reset'


# =================================================================================
# USERS
# =================================================================================

class Role(BaseModel):
    role_name = db.Column(db.String(50), nullable=False, unique=True, index=True)

class User(BaseModel):
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=True, index=True)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, index=True)

    role = db.relationship('Role', backref='users')

    __table_args__ = (
        Index('idx_user_email_phone', 'email', 'phone'),
    )


class Otp(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)

    otp_code = db.Column(db.String(10), nullable=False)
    action = db.Column(db.Enum(OTPAction), nullable=False)
    is_used = db.Column(db.Boolean, default=False, index=True)

    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    __table_args__ = (
        Index('idx_otp_user_action', 'user_id', 'action'),
    )


class Address(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)

    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(20), nullable=False, index=True)

    is_default = db.Column(db.Boolean, default=False)

    __table_args__ = (
        Index('idx_address_user_default', 'user_id', 'is_default'),
    )


# =================================================================================
# PRODUCT
# =================================================================================

class Category(BaseModel):
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)


class Product(BaseModel):
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)

    # ❌ FLOAT hata diya
    price = db.Column(db.Numeric(10, 2), nullable=False)

    stock = db.Column(db.Integer, default=0)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    __table_args__ = (
        CheckConstraint('stock >= 0', name='check_stock_positive'),
    )


class ProductImage(BaseModel):
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    image_url = db.Column(db.String(255), nullable=False)

    is_primary = db.Column(db.Boolean, default=False)

    __table_args__ = (
        Index('idx_product_primary_image', 'product_id', 'is_primary'),
    )


class Specification(BaseModel):
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)

    spec_key = db.Column(db.String(100), nullable=False)
    spec_value = db.Column(db.String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint('product_id', 'spec_key', name='unique_product_spec'),
    )


# =================================================================================
# ORDER
# =================================================================================

class Order(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)

    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    payment_method = db.Column(db.Enum(PaymentMethod))
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.pending, index=True)


class OrderItem(BaseModel):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)

    price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
    )


class Payment(BaseModel):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    transaction_id = db.Column(db.String(100), unique=True)

    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.pending, index=True)


class Coupon(BaseModel):
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)

    discount_percentage = db.Column(db.Float)
    discount_flat = db.Column(db.Numeric(10, 2))

    expiry_date = db.Column(db.DateTime, nullable=False, index=True)


# =================================================================================
# REVIEW
# =================================================================================

class Review(BaseModel):
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        UniqueConstraint('product_id', 'user_id', name='unique_user_review'),
    )