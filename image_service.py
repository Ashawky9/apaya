import os
import uuid
from PIL import Image, ImageOps
from io import BytesIO
from flask import current_app
from werkzeug.utils import secure_filename

class ImageService:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.config = app.config.get('IMAGE_CONFIG')
    
    @staticmethod
    def allowed_file(filename):
        """التحقق من صيغة الملف"""
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    @staticmethod
    def generate_unique_filename(original_filename):
        """إنشاء اسم فريد للملف"""
        ext = original_filename.rsplit('.', 1)[1].lower()
        unique_id = uuid.uuid4().hex
        return f"{unique_id}.{ext}"
    
    @staticmethod
    def get_file_extension(filename):
        """الحصول على امتداد الملف"""
        return filename.rsplit('.', 1)[1].lower()
    
    @staticmethod
    def optimize_image(image, format_type='JPEG'):
        """تحسين جودة الصورة"""
        if format_type.upper() == 'JPEG':
            # تحويل إلى RGB إذا كانت الصورة بـ RGBA
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
        
        return image
    
    def resize_image(self, image, size):
        """تغيير حجم الصورة مع الحفاظ على التناسب"""
        if size is None:
            return image
        
        width, height = size
        
        # الحفاظ على نسبة الطول إلى العرض
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        
        # إنشاء صورة جديدة بخلفية بيضاء للحفاظ على الأبعاد
        if image.size != (width, height):
            new_image = Image.new('RGB', (width, height), (255, 255, 255))
            # وضع الصورة في المنتصف
            offset = ((width - image.size[0]) // 2, (height - image.size[1]) // 2)
            new_image.paste(image, offset)
            image = new_image
        
        return image
    
    def save_image_variants(self, image, filename, folder):
        """حفظ الصورة بجميع الأحجام المطلوبة"""
        variants = {}
        base_name = filename.rsplit('.', 1)[0]
        ext = filename.rsplit('.', 1)[1].lower()
        
        # التأكد من وجود المجلدات
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        
        for size_name, dimensions in self.config.SIZES.items():
            # نسخة من الصورة الأصلية للمعالجة
            processed_image = image.copy()
            
            # تغيير الحجم إذا كان مطلوباً
            if dimensions:
                processed_image = self.resize_image(processed_image, dimensions)
            
            # تحسين الجودة
            processed_image = self.optimize_image(processed_image, ext)
            
            # إنشاء اسم الملف
            if size_name == 'original':
                variant_filename = filename
            else:
                variant_filename = f"{base_name}_{size_name}.{ext}"
            
            # حفظ الصورة
            variant_path = os.path.join(upload_path, variant_filename)
            
            # إعدادات الحفظ بناءً على الصيغة
            save_kwargs = {}
            if ext in ['jpg', 'jpeg']:
                save_kwargs['quality'] = self.config.JPEG_QUALITY
                save_kwargs['optimize'] = True
            elif ext == 'png':
                save_kwargs['compress_level'] = self.config.PNG_COMPRESSION
                save_kwargs['optimize'] = True
            
            processed_image.save(variant_path, **save_kwargs)
            variants[size_name] = variant_filename
        
        return variants
    
    def process_uploaded_image(self, file, folder='products'):
        """معالجة الصورة المرفوعة"""
        if not file or file.filename == '':
            return None
        
        if not self.allowed_file(file.filename):
            raise ValueError('صيغة الملف غير مدعومة')
        
        # فتح الصورة
        try:
            image = Image.open(file.stream)
            
            # التحقق من حجم الملف
            file.seek(0, 2)  # الانتقال إلى نهاية الملف
            file_size = file.tell()
            file.seek(0)  # العودة إلى بداية الملف
            
            if file_size > self.config.MAX_FILE_SIZE:
                raise ValueError('حجم الملف أكبر من المسموح به')
            
            # إنشاء اسم فريد للملف
            original_filename = secure_filename(file.filename)
            unique_filename = self.generate_unique_filename(original_filename)
            
            # حفظ جميع الأحجام
            variants = self.save_image_variants(image, unique_filename, folder)
            
            return variants
            
        except Exception as e:
            current_app.logger.error(f'Error processing image: {str(e)}')
            raise ValueError(f'خطأ في معالجة الصورة: {str(e)}')
    
    def get_image_url(self, filename, folder, size='medium'):
        """الحصول على رابط الصورة بالحجم المطلوب"""
        if not filename or filename == 'default_product.jpg':
            return None
        
        base_name = filename.rsplit('.', 1)[0]
        ext = filename.rsplit('.', 1)[1].lower()
        
        if size == 'original':
            image_filename = filename
        else:
            image_filename = f"{base_name}_{size}.{ext}"
        
        return f"uploads/{folder}/{image_filename}"
    
    def delete_image_variants(self, filename, folder):
        """حذف جميع أحجام الصورة"""
        try:
            base_name = filename.rsplit('.', 1)[0]
            ext = filename.rsplit('.', 1)[1].lower()
            
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
            
            # حذف جميع الأحجام
            for size_name in self.config.SIZES.keys():
                if size_name == 'original':
                    variant_filename = filename
                else:
                    variant_filename = f"{base_name}_{size_name}.{ext}"
                
                variant_path = os.path.join(upload_path, variant_filename)
                if os.path.exists(variant_path):
                    os.remove(variant_path)
                    
        except Exception as e:
            current_app.logger.error(f'Error deleting image variants: {str(e)}')

# إنشاء نسخة من الخدمة
image_service = ImageService()