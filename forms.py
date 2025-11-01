from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, MultipleFileField, BooleanField, TextAreaField, FloatField, IntegerField, SelectField, FileField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from flask_wtf.file import FileAllowed, FileSize
from models import User
from config import ImageConfig

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class RegisterForm(FlaskForm):
    first_name = StringField('الاسم الأول', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('اسم العائلة', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('تأكيد كلمة المرور', 
                                  validators=[DataRequired(), EqualTo('password')])
    agree_terms = BooleanField('أوافق على الشروط والأحكام', validators=[DataRequired()])
    submit = SubmitField('تسجيل')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('اسم المستخدم موجود مسبقا، اختر اسم آخر')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('البريد الإلكتروني موجود مسبقا، اختر بريد آخر')

class ProductForm(FlaskForm):
    name = StringField('اسم المنتج', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('الوصف', validators=[DataRequired()])
    price = FloatField('السعر', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('التصنيف', choices=[
        ('عبايات', 'عبايات'),
        ('حجابات', 'حجابات'),
        ('أكسسوارات', 'أكسسوارات'),
        ('عروض خاصة', 'عروض خاصة')
    ], validators=[DataRequired()])
    stock = IntegerField('الكمية المتاحة', validators=[DataRequired(), NumberRange(min=0)])
    discount = IntegerField('الخصم (%)', validators=[NumberRange(min=0, max=100)], default=0)
    images = MultipleFileField('صور المنتج', validators=[
        FileAllowed(ImageConfig.ALLOWED_EXTENSIONS, 'الصيغ المدعومة: JPG, PNG, GIF, WEBP, BMP'),
        FileSize(max_size=ImageConfig.MAX_FILE_SIZE, message=f'الحجم الأقصى للملف: {ImageConfig.MAX_FILE_SIZE // (1024*1024)}MB')
    ], render_kw={'multiple': True, 'accept': 'image/*'})
    is_active = BooleanField('نشط', default=True)
    submit = SubmitField('حفظ')

class OfferForm(FlaskForm):
    title = StringField('عنوان العرض', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('وصف العرض', validators=[DataRequired()])
    discount_percentage = IntegerField('نسبة الخصم %', validators=[DataRequired(), NumberRange(min=1, max=100)])
    original_price = FloatField('السعر الأصلي', validators=[DataRequired(), NumberRange(min=0)])
    offer_price = FloatField('سعر العرض', validators=[Optional(), NumberRange(min=0)])
    image = FileField('صورة العرض', validators=[
        FileAllowed(ImageConfig.ALLOWED_EXTENSIONS, 'الصيغ المدعومة: JPG, PNG, GIF, WEBP, BMP'),
        FileSize(max_size=ImageConfig.MAX_FILE_SIZE, message=f'الحجم الأقصى للملف: {ImageConfig.MAX_FILE_SIZE // (1024*1024)}MB')
    ], render_kw={'accept': 'image/*'})
    start_date = DateTimeField('تاريخ البدء', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_date = DateTimeField('تاريخ الانتهاء', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('حفظ العرض')

class ContactForm(FlaskForm):
    name = StringField('الاسم بالكامل', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    subject = StringField('الموضوع', validators=[DataRequired(), Length(min=5, max=200)])
    message = TextAreaField('الرسالة', validators=[DataRequired(), Length(min=10, max=1000)])
    submit = SubmitField('إرسال الرسالة')

class CheckoutForm(FlaskForm):
    full_name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    phone = StringField('رقم الهاتف', validators=[DataRequired(), Length(min=10, max=15)])
    address = TextAreaField('عنوان الشحن', validators=[DataRequired(), Length(min=10, max=500)])
    city = StringField('المدينة', validators=[DataRequired(), Length(max=50)])
    country = StringField('البلد', validators=[DataRequired(), Length(max=50)])
    payment_method = SelectField('طريقة الدفع', choices=[
        ('credit_card', 'بطاقة ائتمان'),
        ('cash_on_delivery', 'الدفع عند الاستلام')
    ], validators=[DataRequired()])
    submit = SubmitField('تأكيد الطلب')

class AccountUpdateForm(FlaskForm):
    first_name = StringField('الاسم الأول', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('اسم العائلة', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    phone = StringField('رقم الهاتف', validators=[Optional(), Length(max=20)])
    address = TextAreaField('العنوان', validators=[Optional(), Length(max=500)])
    city = StringField('المدينة', validators=[Optional(), Length(max=100)])
    country = StringField('البلد', validators=[Optional(), Length(max=100)])
    submit = SubmitField('تحديث المعلومات')

class PasswordUpdateForm(FlaskForm):
    current_password = PasswordField('كلمة المرور الحالية', validators=[DataRequired()])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', 
                                   validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('تغيير كلمة المرور')