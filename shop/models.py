import uuid
import enum
from datetime import datetime, timedelta
from shop.extensions import db

# =================================================================================
# 💎 ENUMS (Strict Data Types)
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
# 🔁 BASE MODEL (Super Trick: Ye 8 fields har table me auto-add ho jayengi)
# =================================================================================
class BaseModel(db.Model):
    __abstract__ = True  # Ye batata hai ki iski khud ki koi table nahi banegi

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # 6 MANDATORY FIELDS (Auditing)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, nullable=True) # Integer is safe here
    updated_by = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=db.func.now())


# =================================================================================
# 🔐 MODULE 1 & 2: AUTH, USERS & ADMIN
# =================================================================================

class Role(BaseModel):
    __tablename__ = 'roles'
    role_name = db.Column(db.String(50), nullable=False, unique=True)
    users = db.relationship('User', back_populates='role', lazy=True)

class User(BaseModel):
    __tablename__ = 'users'
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False) 
    is_verified = db.Column(db.Boolean, default=False)

    role = db.relationship('Role', back_populates='users')
    addresses = db.relationship('Address', backref='user', lazy=True)
    otps = db.relationship('Otp', backref='user', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    products = db.relationship('Product', backref='seller_user', lazy=True)

class Otp(BaseModel):
    __tablename__ = 'otps'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    otp_code = db.Column(db.String(10), nullable=False)
    action = db.Column(db.Enum(OTPAction), default=OTPAction.verification)
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))

class Address(BaseModel):
    __tablename__ = 'addresses'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    is_default = db.Column(db.Boolean, default=False)


# =================================================================================
# 📦 MODULE 3 & 6: CATALOG, PRODUCTS & SELLER
# =================================================================================

class Category(BaseModel):
    __tablename__ = 'categories'
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    products = db.relationship('Product', backref='category', lazy=True)

class SellerCategory(BaseModel):
    __tablename__ = 'seller_categories'
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=True)

class Product(BaseModel):
    __tablename__ = 'products'
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    images = db.relationship('ProductImage', backref='product', cascade="all, delete-orphan", lazy=True)
    specifications = db.relationship('Specification', backref='product', cascade="all, delete-orphan", lazy=True)
    reviews = db.relationship('Review', backref='product', lazy=True)

class ProductImage(BaseModel):
    __tablename__ = 'product_images'
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)

class Specification(BaseModel):
    __tablename__ = 'specifications'
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    spec_key = db.Column(db.String(100), nullable=False)   
    spec_value = db.Column(db.String(255), nullable=False) 


# =================================================================================
# 🛒 MODULE 4, 5 & 9: CART, ORDERS, PAYMENT & DISCOUNT
# =================================================================================

class Coupon(BaseModel):
    __tablename__ = 'coupons'
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=True) 
    discount_flat = db.Column(db.Float, nullable=True)       
    expiry_date = db.Column(db.DateTime, nullable=False)

class CartItem(BaseModel):
    __tablename__ = 'cart_items'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    product = db.relationship('Product', lazy=True)

class Order(BaseModel):
    __tablename__ = 'orders'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False) 
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=True)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.pending) 

    items = db.relationship('OrderItem', backref='order', cascade="all, delete-orphan", lazy=True)
    tracking = db.relationship('OrderTracking', backref='order', cascade="all, delete-orphan", lazy=True)
    payment = db.relationship('Payment', backref='order', uselist=False, lazy=True) 
    invoice = db.relationship('Invoice', backref='order', uselist=False, lazy=True) 

class OrderItem(BaseModel):
    __tablename__ = 'order_items'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False) 
    product = db.relationship('Product', lazy=True)

class Payment(BaseModel):
    __tablename__ = 'payments'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=True) 
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.pending)

class Invoice(BaseModel):
    __tablename__ = 'invoices'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    pdf_url = db.Column(db.String(255), nullable=True) 

class OrderTracking(BaseModel):
    __tablename__ = 'order_tracking'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    status = db.Column(db.Enum(OrderStatus), nullable=False)
    message = db.Column(db.String(255), nullable=True) 


# =================================================================================
# ⭐ MODULE 7: WISHLIST & REVIEW
# =================================================================================

class Wishlist(BaseModel):
    __tablename__ = 'wishlists'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

class Review(BaseModel):
    __tablename__ = 'reviews'
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1 to 5
    comment = db.Column(db.Text, nullable=True)