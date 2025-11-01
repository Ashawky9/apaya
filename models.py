from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    work_address = db.Column(db.Text)
    work_city = db.Column(db.String(100))
    work_country = db.Column(db.String(100))
    work_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    cart_items = db.relationship('Cart', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref=db.backref('images', lazy=True, cascade='all, delete-orphan'))
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=0)
    discount = db.Column(db.Float, default=0.0)  # تأكد من وجود هذا الحقل
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    carts = db.relationship('Cart', backref='product', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def is_in_stock(self):
        return self.stock > 0
    
    def get_display_price(self):
        return f'{self.price:.2f}'
    
    # أضف هذه الخصائص للحفاظ على التوافق مع الكود القديم
    @property
    def image(self):
        """خاصية للتوافق مع الكود القديم الذي يستخدم product.image"""
        if self.images:
            # إرجاع الصورة الأساسية أو أول صورة
            primary_image = next((img for img in self.images if img.is_primary), None)
            if primary_image:
                return primary_image.image_url
            return self.images[0].image_url
        return 'default_product.jpg'
    
    @property
    def primary_image(self):
        """الحصول على الصورة الأساسية"""
        if self.images:
            primary = next((img for img in self.images if img.is_primary), None)
            if primary:
                return primary.image_url
            return self.images[0].image_url
        return 'default_product.jpg'
    
    
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Cart {self.user_id} - {self.product_id}>'
    
    def get_total_price(self):
        return self.product.price * self.quantity
    
    def get_display_total_price(self):
        return f'{self.get_total_price():.2f}'

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    discount_percentage = db.Column(db.Integer, nullable=False)
    original_price = db.Column(db.Float, nullable=False)
    offer_price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), default='default_offer.jpg')
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(days=7))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Offer('{self.title}', '{self.discount_percentage}%')"
    
    def is_active_now(self):
        now = datetime.utcnow()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def get_display_original_price(self):
        return f'{self.original_price:.2f}'
    
    def get_display_offer_price(self):
        return f'{self.offer_price:.2f}'

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<ContactMessage {self.subject} - {self.email}>"
    
    def get_created_date(self):
        return self.created_at.strftime('%Y-%m-%d %H:%M')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    shipping_address = db.Column(db.Text)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(120))
    customer_phone = db.Column(db.String(20))
    
    # العلاقة مع العناصر
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.id} - {self.user_id}>'
    
    def get_status_display(self):
        statuses = {
            'pending': 'قيد الانتظار',
            'processing': 'قيد المعالجة',
            'shipped': 'تم الشحن',
            'delivered': 'تم التوصيل',
            'cancelled': 'ملغي'
        }
        return statuses.get(self.status, self.status)
    
    def get_order_date(self):
        return self.order_date.strftime('%Y-%m-%d %H:%M')
    
    def get_display_total_amount(self):
        return f'{self.total_amount:.2f}'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<OrderItem {self.id} - Order {self.order_id}>'
    
    def get_total_price(self):
        return self.price * self.quantity
    
    def get_display_price(self):
        return f'{self.price:.2f}'
    
    def get_display_total_price(self):
        return f'{self.get_total_price():.2f}'