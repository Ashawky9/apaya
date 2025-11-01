import os
from datetime import timedelta

# المسارات الأساسية
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

# إعدادات الصور
class ImageConfig:
    # الصيغ المدعومة
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
    
    # الحجم الأقصى للملف (10 ميجابايت)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # إعدادات الصور المصغرة
    THUMBNAIL_SIZE = (300, 300)
    MEDIUM_SIZE = (600, 600)
    LARGE_SIZE = (1200, 1200)
    
    # جودة الضغط
    JPEG_QUALITY = 85
    PNG_COMPRESSION = 6
    
    # المجلدات
    PRODUCTS_FOLDER = 'products'
    OFFERS_FOLDER = 'offers'
    USERS_FOLDER = 'users'
    
    # الأحجام المطلوبة لكل نوع
    SIZES = {
        'thumbnail': (300, 300),
        'medium': (600, 600),
        'large': (1200, 1200),
        'original': None  # الحجم الأصلي
    }

# إعدادات التطبيق الأساسية
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///abaya_store.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # تحميل الملفات
    UPLOAD_FOLDER = UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = ImageConfig.MAX_FILE_SIZE
    
    # البريد الإلكتروني
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # الجلسات
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # التخزين المؤقت
    CACHE_TYPE = 'simple'