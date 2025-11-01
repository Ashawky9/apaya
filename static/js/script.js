// كود JavaScript للمتجر

document.addEventListener('DOMContentLoaded', function() {
    // تحديث عدد العناصر في السلة
    updateCartCount();
    
    // إعداد المنبثقات (Tooltips)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // إعداد النماذج
    setupForms();
    
    // إعداد معرض الصور
    setupImageGallery();
});

// تحديث عدد العناصر في السلة
function updateCartCount() {
    const cartCount = document.querySelector('.cart-count');
    if (cartCount) {
        // يمكن جلب عدد العناصر من localStorage أو من الخادم
        const cartItems = JSON.parse(localStorage.getItem('cartItems')) || [];
        cartCount.textContent = cartItems.length;
    }
}

// إعداد النماذج
function setupForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // التحقق من صحة النموذج قبل الإرسال
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            this.classList.add('was-validated');
        });
    });
}

// إعداد معرض الصور
function setupImageGallery() {
    const thumbnails = document.querySelectorAll('.thumbnail-images .thumb img');
    
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            const mainImage = document.getElementById('main-product-image');
            if (mainImage) {
                mainImage.src = this.src;
                
                // إضافة تأثير التغيير
                mainImage.style.opacity = '0';
                setTimeout(() => {
                    mainImage.style.opacity = '1';
                }, 150);
            }
        });
    });
}

// وظيفة لإضافة منتج إلى السلة
function addToCart(productId, productName, productPrice, productImage, quantity = 1) {
    let cartItems = JSON.parse(localStorage.getItem('cartItems')) || [];
    
    // التحقق إذا كان المنتج موجوداً بالفعل في السلة
    const existingItemIndex = cartItems.findIndex(item => item.id === productId);
    
    if (existingItemIndex > -1) {
        // زيادة الكمية إذا كان المنتج موجوداً
        cartItems[existingItemIndex].quantity += quantity;
    } else {
        // إضافة منتج جديد إلى السلة
        cartItems.push({
            id: productId,
            name: productName,
            price: productPrice,
            image: productImage,
            quantity: quantity
        });
    }
    
    // حفظ السلة في localStorage
    localStorage.setItem('cartItems', JSON.stringify(cartItems));
    
    // تحديث عدد العناصر في السلة
    updateCartCount();
    
    // إظهار رسالة نجاح
    showAlert('تمت إضافة المنتج إلى سلة التسوق', 'success');
}

// وظيفة لإظهار رسائل التنبيه
function showAlert(message, type = 'info') {
    // إنصراف عن التنبيه المضمن إذا كان موجوداً
    const existingAlert = document.querySelector('.alert-dismissible');
    if (existingAlert) {
        const alert = new bootstrap.Alert(existingAlert);
        alert.close();
    }
    
    // إنشاء عنصر التنبيه
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.style.minWidth = '300px';
    alertDiv.style.textAlign = 'center';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // إضافة التنبيه إلى body
    document.body.appendChild(alertDiv);
    
    // إخفاء التنبيه تلقائياً بعد 3 ثوان
    setTimeout(() => {
        const alert = new bootstrap.Alert(alertDiv);
        alert.close();
    }, 3000);
}

// وظيفة للبحث عن المنتجات
function searchProducts(query) {
    // يمكن تنفيذ البحث من خلال AJAX أو إعادة توجيه إلى صفحة البحث
    window.location.href = `/search?q=${encodeURIComponent(query)}`;
}

// وظيفة للتصفية حسب الفئة
function filterByCategory(category) {
    const url = new URL(window.location.href);
    url.searchParams.set('category', category);
    window.location.href = url.toString();
}

// وظيفة للترتيب حسب
function sortProducts(sortBy) {
    const url = new URL(window.location.href);
    url.searchParams.set('sort', sortBy);
    window.location.href = url.toString();
}

// وظيفة لإضافة المنتج إلى المفضلة
function addToWishlist(productId) {
    let wishlist = JSON.parse(localStorage.getItem('wishlist')) || [];
    
    if (!wishlist.includes(productId)) {
        wishlist.push(productId);
        localStorage.setItem('wishlist', JSON.stringify(wishlist));
        showAlert('تمت إضافة المنتج إلى المفضلة', 'success');
    } else {
        showAlert('المنتج موجود بالفعل في المفضلة', 'info');
    }
}

// وظيفة لمشاركة المنتج
function shareProduct(productId, platform) {
    const productUrl = `${window.location.origin}/product/${productId}`;
    let shareUrl = '';
    
    switch(platform) {
        case 'facebook':
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(productUrl)}`;
            break;
        case 'twitter':
            shareUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(productUrl)}`;
            break;
        case 'whatsapp':
            shareUrl = `https://wa.me/?text=${encodeURIComponent('انظر إلى هذا المنتج: ' + productUrl)}`;
            break;
        default:
            // نسخ الرابط
            navigator.clipboard.writeText(productUrl).then(() => {
                showAlert('تم نسخ رابط المنتج', 'success');
            });
            return;
    }
    
    window.open(shareUrl, '_blank');
}
// وظائف خاصة بصفحة نتائج البحث
function initSearchPage() {
    // حفظ آخر بحث للمستخدم
    const searchQuery = document.querySelector('input[name="q"]').value;
    if (searchQuery) {
        localStorage.setItem('lastSearch', searchQuery);
    }
    
    // تحميل آخر بحث عند العودة للصفحة
    const lastSearch = localStorage.getItem('lastSearch');
    if (lastSearch && !searchQuery) {
        document.querySelector('input[name="q"]').value = lastSearch;
    }
    
    // تصفية النتائج بدون إعادة تحميل الصفحة (AJAX)
    setupSearchFilters();
}

// إعداد فلاتر البحث
function setupSearchFilters() {
    const categoryFilter = document.querySelector('select[name="category"]');
    const sortFilter = document.querySelector('select#sortResults');
    
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            this.form.submit();
        });
    }
    
    if (sortFilter) {
        sortFilter.addEventListener('change', function() {
            // إضافة معامل الترتيب إلى URL وإعادة التوجيه
            const url = new URL(window.location.href);
            url.searchParams.set('sort', this.value);
            window.location.href = url.toString();
        });
    }
}

// البحث الآني (إذا كان مدعوماً من الخادم)
function setupLiveSearch() {
    const searchInput = document.querySelector('input[name="q"]');
    const searchResults = document.getElementById('search-results');
    
    if (searchInput && searchResults) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            if (this.value.length > 2) {
                searchTimeout = setTimeout(() => {
                    fetchLiveSearchResults(this.value);
                }, 500);
            }
        });
    }
}

// جلب نتائج البحث الآني (AJAX)
function fetchLiveSearchResults(query) {
    fetch(`/api/search/suggest?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displayLiveSearchResults(data);
        })
        .catch(error => {
            console.error('Error fetching search results:', error);
        });
}

// عرض نتائج البحث الآني
function displayLiveSearchResults(results) {
    const container = document.getElementById('live-search-results');
    if (!container) return;
    
    if (results.length > 0) {
        container.innerHTML = results.map(product => `
            <a href="/product/${product.id}" class="list-group-item list-group-item-action">
                <div class="d-flex align-items-center">
                    <img src="/static/images/products/${product.image}" alt="${product.name}" width="40" height="40" class="me-3">
                    <div>
                        <h6 class="mb-0">${product.name}</h6>
                        <small class="text-muted">${product.price} ر.س</small>
                    </div>
                </div>
            </a>
        `).join('');
        
        container.classList.remove('d-none');
    } else {
        container.classList.add('d-none');
    }
}

// إخفاء نتائج البحث الآني عند فقدان التركيز
document.addEventListener('click', function(e) {
    const liveResults = document.getElementById('live-search-results');
    const searchInput = document.querySelector('input[name="q"]');
    
    if (liveResults && searchInput && !searchInput.contains(e.target) && !liveResults.contains(e.target)) {
        liveResults.classList.add('d-none');
    }
});

// تهيئة صفحة البحث عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('input[name="q"]')) {
        initSearchPage();
        setupLiveSearch();
    }
});

// تأثيرات تفاعلية للبنر
document.addEventListener('DOMContentLoaded', function() {
    const imageWrapper = document.querySelector('.royal-image-wrapper');
    const image = document.querySelector('.animated-image');
    
    if (imageWrapper && image) {
        // تأثير الحركة بالماوس
        imageWrapper.addEventListener('mousemove', function(e) {
            const xAxis = (window.innerWidth / 2 - e.pageX) / 25;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 25;
            
            imageWrapper.style.transform = `perspective(1000px) rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
        });
        
        // إعادة الصورة إلى وضعها الطبيعي عند مغادرة الماوس
        imageWrapper.addEventListener('mouseleave', function() {
            imageWrapper.style.transform = 'perspective(1000px) rotateY(-5deg)';
            image.style.transform = 'scale(1)';
        });
        
        // تأثير الدخول عند التمرير إلى البنر
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, { threshold: 0.3 });
        
        observer.observe(imageWrapper);
    }
    
    // تأثير كتابة النص (إذا desired)
    const titleElement = document.querySelector('.royal-title');
    if (titleElement) {
        const text = titleElement.textContent;
        titleElement.textContent = '';
        
        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                titleElement.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            }
        };
        
        // تفعيل تأثير الكتابة عند التمرير إلى العنصر
        const titleObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    typeWriter();
                    titleObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        titleObserver.observe(titleElement);
    }
});