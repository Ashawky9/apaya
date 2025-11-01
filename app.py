import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from flask_migrate import Migrate

from extensions import db, login_manager, mail
from forms import LoginForm, RegisterForm, ProductForm, OfferForm, ContactForm
from models import User, Product, Cart, Offer, Order, OrderItem, ContactMessage, ProductImage
from image_service import ImageService
from config import Config, ImageConfig
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
app.config['IMAGE_CONFIG'] = ImageConfig()
image_service = ImageService()
# تهيئة الامتدادات
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
mail.init_app(app)
image_service.init_app(app)
migrate = Migrate(app, db)

# إنشاء المجلدات المطلوبة
with app.app_context():
    # إنشاء مجلدات التحميل
    folders = [
        os.path.join(app.config['UPLOAD_FOLDER'], ImageConfig.PRODUCTS_FOLDER),
        os.path.join(app.config['UPLOAD_FOLDER'], ImageConfig.OFFERS_FOLDER),
        os.path.join(app.config['UPLOAD_FOLDER'], ImageConfig.USERS_FOLDER)
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)


# إنشاء الجداول عند التشغيل الأول
with app.app_context():
    db.create_all()
    # إنشاء مستخدم أدمن إذا لم يكن موجود
    if not User.query.filter_by(username='admin').first():
        admin = User(
            first_name='Admin',
            last_name='User',
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

# تحميل المستخدم
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# دالة للتحقق من أن المستخدم أدمن
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# المسارات الأساسية
@app.route('/')
def index():
    products = Product.query.order_by(Product.created_at.desc()).limit(4).all()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('تمت إضافة المنتج إلى سلة التسوق', 'success')
    return redirect(request.referrer)

@app.route('/update_cart/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.user_id != current_user.id:
        abort(403)
    
    action = request.form.get('action')
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
    elif action == 'remove':
        db.session.delete(cart_item)
    
    db.session.commit()
    flash('تم تحديث سلة التسوق', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('سلة التسوق فارغة', 'warning')
        return redirect(url_for('cart'))
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/process_order', methods=['POST'])
@login_required
def process_order():
    # جمع بيانات الطلب من النموذج
    payment_method = request.form.get('payment_method')
    shipping_address = request.form.get('shipping_address')
    
    # الحصول على عناصر السلة
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('سلة التسوق فارغة', 'warning')
        return redirect(url_for('cart'))
    
    # حساب الإجمالي
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    # إنشاء الطلب
    order = Order(
        user_id=current_user.id,
        total_amount=total,
        payment_method=payment_method,
        shipping_address=shipping_address
    )
    db.session.add(order)
    db.session.commit()
    
    # إضافة عناصر الطلب
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_item)
        # تقليل الكمية المتاحة من المنتج
        product = Product.query.get(item.product_id)
        product.stock -= item.quantity
        # حذف العنصر من السلة
        db.session.delete(item)
    
    db.session.commit()
    flash('تم إنشاء الطلب بنجاح', 'success')
    return redirect(url_for('order_confirmation', order_id=order.id))

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    return render_template('order_confirmation.html', order=order)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            username=form.username.data,
            email=form.email.data,
            is_admin=False  # المستخدمون الجدد ليسوا مدراء
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('تم تسجيل حسابك بنجاح! يمكنك الآن تسجيل الدخول', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# صفحة "من نحن"
@app.route('/about')
def about():
    return render_template('about.html', 
                         page_title="من نحن - متجر العبايات",
                         active_page='about')

# صفحة "اتصل بنا" - مع نموذج التواصل
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        subject = form.subject.data
        message = form.message.data
        
        try:
            # إرسال البريد الإلكتروني
            msg = Message(
                subject=f"رسالة جديدة من متجر العبايات: {subject}",
                recipients=['info@abaya-store.com'],  # البريد الذي تستقبل عليه الرسائل
                body=f"""
                اسم المرسل: {name}
                البريد الإلكتروني: {email}
                الموضوع: {subject}
                
                الرسالة:
                {message}
                """
            )
            mail.send(msg)
            
            # حفظ الرسالة في قاعدة البيانات
            contact_message = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(contact_message)
            db.session.commit()
            
            flash('تم إرسال رسالتك بنجاح. سنتواصل معك قريباً!', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            flash('حدث خطأ أثناء إرسال الرسالة. يرجى المحاولة مرة أخرى.', 'danger')
            print(f"Error sending email: {e}")
    
    return render_template('contact.html', 
                         page_title="اتصل بنا - متجر العبايات",
                         active_page='contact',
                         form=form)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', 
                         page_title="سياسة الخصوصية - متجر العبايات",
                         active_page='privacy')

@app.route('/terms')
def terms():
    return render_template('terms.html', 
                         page_title="الشروط والأحكام - متجر العبايات",
                         active_page='terms')

@app.route('/offers')
def offers():
    active_offers = Offer.query.filter_by(is_active=True).filter(Offer.end_date >= datetime.now()).all()
    return render_template('offers.html', offers=active_offers)

@app.route('/account')
@login_required
def account():
    # جلب طلبات المستخدم
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_date.desc()).all()
    return render_template('account.html', orders=orders)

@app.route('/update_account', methods=['POST'])
@login_required
def update_account():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.email = request.form.get('email')
        current_user.phone = request.form.get('phone')
        current_user.username = request.form.get('username')
        
        # تغيير كلمة المرور إذا تم تقديمها
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            if current_user.check_password(current_password):
                if new_password == confirm_password:
                    current_user.set_password(new_password)
                    flash('تم تحديث كلمة المرور بنجاح', 'success')
                else:
                    flash('كلمة المرور الجديدة غير متطابقة', 'danger')
            else:
                flash('كلمة المرور الحالية غير صحيحة', 'danger')
        
        db.session.commit()
        flash('تم تحديث معلومات الحساب بنجاح', 'success')
        return redirect(url_for('account'))

@app.route('/update_address', methods=['POST'])
@login_required
def update_address():
    if request.method == 'POST':
        current_user.address = request.form.get('address')
        current_user.city = request.form.get('city')
        current_user.country = request.form.get('country')
        current_user.phone = request.form.get('phone')
        
        db.session.commit()
        flash('تم تحديث العنوان بنجاح', 'success')
        return redirect(url_for('account'))

@app.route('/update_work_address', methods=['POST'])
@login_required
def update_work_address():
    if request.method == 'POST':
        current_user.work_address = request.form.get('work_address')
        current_user.work_city = request.form.get('work_city')
        current_user.work_country = request.form.get('work_country')
        current_user.work_phone = request.form.get('work_phone')
        
        db.session.commit()
        flash('تم تحديث عنوان العمل بنجاح', 'success')
        return redirect(url_for('account'))

# مسار تتبع الطلب
@app.route('/track_order')
def track_order():
    return render_template('track_order.html', 
                         page_title="تتبع الطلب - متجر العبايات",
                         active_page='track_order')

# سياسة الإرجاع
@app.route('/return_policy')
def return_policy():
    return render_template('return_policy.html', 
                         page_title="سياسة الإرجاع - متجر العبايات",
                         active_page='return_policy')

# الأسئلة الشائعة
@app.route('/faq')
def faq():
    return render_template('faq.html', 
                         page_title="الأسئلة الشائعة - متجر العبايات",
                         active_page='faq')

# لوحة تحكم الأدمن
@app.route('/admin')
@admin_required
def admin_dashboard():
    total_products = Product.query.count()
    total_users = User.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    latest_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    latest_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         total_products=total_products,
                         total_users=total_users,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         latest_products=latest_products,
                         latest_orders=latest_orders)

# إدارة المنتجات
@app.route('/admin/products')
@admin_required
def admin_products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('admin/products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            stock=form.stock.data,
            discount=form.discount.data,
            is_active=form.is_active.data
        )
        db.session.add(product)
        db.session.flush()  # للحصول على ID المنتج
        
        # معالجة الصور المرفوعة
        images = form.images.data
        if images and images[0].filename != '':
            for i, image_file in enumerate(images):
                if image_file and image_file.filename != '':
                    try:
                        # معالجة الصورة باستخدام الخدمة
                        image_variants = image_service.process_uploaded_image(
                            image_file, 
                            ImageConfig.PRODUCTS_FOLDER
                        )
                        
                        # حفظ معلومات الصورة في قاعدة البيانات
                        product_image = ProductImage(
                            product_id=product.id,
                            image_url=image_variants['original'],  # حفظ اسم الملف الأصلي
                            is_primary=(i == 0)  # أول صورة هي الأساسية
                        )
                        db.session.add(product_image)
                        
                    except ValueError as e:
                        flash(f'خطأ في معالجة الصورة: {str(e)}', 'danger')
                        db.session.rollback()
                        return render_template('admin/add_product.html', form=form)
                    except Exception as e:
                        flash('حدث خطأ غير متوقع في معالجة الصورة', 'danger')
                        app.logger.error(f'Unexpected error processing image: {str(e)}')
                        db.session.rollback()
                        return render_template('admin/add_product.html', form=form)
        
        db.session.commit()
        flash('تمت إضافة المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/add_product.html', form=form)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.category = form.category.data
        product.stock = form.stock.data
        product.discount = form.discount.data
        product.is_active = form.is_active.data
        
        # معالجة الصور الجديدة
        images = form.images.data
        if images and images[0].filename != '':
            for i, image in enumerate(images):
                if image and image.filename != '':
                    filename = secure_filename(f"{product.id}_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename}")
                    products_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products')
                    os.makedirs(products_dir, exist_ok=True)
                    
                    image_path = os.path.join(products_dir, filename)
                    image.save(image_path)
                    
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=filename,
                        is_primary=False  # لا نجعلها أساسية تلقائياً
                    )
                    db.session.add(product_image)
        
        db.session.commit()
        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html', form=form, product=product)

@app.route('/admin/product/delete/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    try:
        # حذف جميع الصور المرتبطة بالمنتج من الخادم
        for image in product.images:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'products', image.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # حذف المنتج من قاعدة البيانات (سيحذف تلقائياً الصور المرتبطة به بسبب cascade)
        db.session.delete(product)
        db.session.commit()
        flash('تم حذف المنتج بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف المنتج', 'danger')
        app.logger.error(f'Error deleting product: {e}')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/product/set_primary_image/<int:image_id>', methods=['POST'])
@admin_required
def set_primary_image(image_id):
    image = ProductImage.query.get_or_404(image_id)
    
    # إلغاء تعيين جميع الصور كأساسية
    ProductImage.query.filter_by(product_id=image.product_id).update({'is_primary': False})
    
    # تعيين الصورة المحددة كأساسية
    image.is_primary = True
    db.session.commit()
    
    flash('تم تعيين الصورة كأساسية', 'success')
    return redirect(url_for('edit_product', id=image.product_id))

# مسار لعرض لوحة تحكم العروض (للمسؤولين فقط)
@app.route('/admin/offers')
@admin_required
def admin_offers():
    all_offers = Offer.query.order_by(Offer.created_at.desc()).all()
    return render_template('offers.html', offers=all_offers)

# مسار لإضافة عرض جديد
@app.route('/admin/offer/add', methods=['GET', 'POST'])
@admin_required
def add_offer():
    form = OfferForm()
    if form.validate_on_submit():
        try:
            # حساب سعر العرض تلقائياً إذا لم يتم تقديمه
            offer_price = form.offer_price.data
            if not offer_price:
                offer_price = form.original_price.data * (1 - form.discount_percentage.data / 100)
            
            offer = Offer(
                title=form.title.data,
                description=form.description.data,
                discount_percentage=form.discount_percentage.data,
                original_price=form.original_price.data,
                offer_price=offer_price,
                start_date=form.start_date.data,
                end_date=form.end_date.data
            )
            
            # معالجة صورة العرض إذا تم رفعها
            image_file = request.files.get('image')
            if image_file and image_file.filename != '':
                try:
                    image_variants = image_service.process_uploaded_image(
                        image_file, 
                        ImageConfig.OFFERS_FOLDER
                    )
                    offer.image = image_variants['original']
                except ValueError as e:
                    flash(f'خطأ في معالجة صورة العرض: {str(e)}', 'danger')
                    return render_template('admin/add_offer.html', form=form)
            
            db.session.add(offer)
            db.session.commit()
            flash('تمت إضافة العرض بنجاح', 'success')
            return redirect(url_for('admin_offers'))
            
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إضافة العرض', 'danger')
            app.logger.error(f'Error adding offer: {str(e)}')
    
    return render_template('admin/add_offer.html', form=form)

# مسار لتعديل عرض
@app.route('/admin/offer/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_offer(id):
    offer = Offer.query.get_or_404(id)
    form = OfferForm(obj=offer)
    
    if form.validate_on_submit():
        offer.title = form.title.data
        offer.description = form.description.data
        offer.discount_percentage = form.discount_percentage.data
        offer.original_price = form.original_price.data
        offer.offer_price = form.offer_price.data
        offer.start_date = form.start_date.data
        offer.end_date = form.end_date.data
        
        db.session.commit()
        flash('تم تحديث العرض بنجاح', 'success')
        return redirect(url_for('admin_offers'))
    
    return render_template('admin/edit_offer.html', form=form, offer=offer)

# مسار لحذف عرض
@app.route('/admin/offer/delete/<int:id>', methods=['POST'])
@admin_required
def delete_offer(id):
    offer = Offer.query.get_or_404(id)
    db.session.delete(offer)
    db.session.commit()
    flash('تم حذف العرض بنجاح', 'success')
    return redirect(url_for('admin_offers'))

# مسار لتغيير حالة العرض (تفعيل/تعطيل)
@app.route('/admin/offer/toggle/<int:id>', methods=['POST'])
@admin_required
def toggle_offer(id):
    offer = Offer.query.get_or_404(id)
    offer.is_active = not offer.is_active
    db.session.commit()
    
    status = "مفعل" if offer.is_active else "معطل"
    flash(f'تم {status} العرض بنجاح', 'success')
    return redirect(url_for('admin_offers'))

# إدارة المستخدمين
@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/admin/user/toggle_admin/<int:id>', methods=['POST'])
@admin_required
def toggle_admin(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('لا يمكنك تعديل صلاحياتك الخاصة', 'danger')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        status = 'مدير' if user.is_admin else 'مستخدم عادي'
        flash(f'تم تغيير صلاحيات المستخدم إلى {status}', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/delete/<int:id>', methods=['POST'])
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('تم حذف المستخدم بنجاح', 'success')
    return redirect(url_for('admin_users'))

# إدارة الطلبات
@app.route('/admin/orders')
@admin_required
def admin_orders():
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        orders = Order.query.order_by(Order.order_date.desc()).all()
    else:
        orders = Order.query.filter_by(status=status_filter).order_by(Order.order_date.desc()).all()
    
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)

@app.route('/admin/order/<int:id>')
@admin_required
def admin_order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/order/update_status/<int:id>', methods=['POST'])
@admin_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash('تم تحديث حالة الطلب بنجاح', 'success')
    else:
        flash('حالة الطلب غير صالحة', 'danger')
    
    return redirect(url_for('admin_order_detail', id=id))

# إدارة رسائل التواصل
@app.route('/admin/messages')
@admin_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)

@app.route('/admin/message/<int:id>')
@admin_required
def admin_message_detail(id):
    message = ContactMessage.query.get_or_404(id)
    # وضع علامة على الرسالة كمقروءة
    if not message.is_read:
        message.is_read = True
        db.session.commit()
    return render_template('admin/message_detail.html', message=message)

@app.route('/admin/message/delete/<int:id>', methods=['POST'])
@admin_required
def delete_message(id):
    message = ContactMessage.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()
    flash('تم حذف الرسالة بنجاح', 'success')
    return redirect(url_for('admin_messages'))

if __name__ == '__main__':
    # إنشاء مجلد التحميل إذا لم يكن موجوداً
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'products')
    os.makedirs(upload_dir, exist_ok=True)
    
    app.run(debug=True)