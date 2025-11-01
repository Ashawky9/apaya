// كود JavaScript لإدارة سلة التسوق

document.addEventListener('DOMContentLoaded', function() {
    loadCartItems();
    setupCartEvents();
});

// تحميل عناصر السلة
function loadCartItems() {
    const cartItems = JSON.parse(localStorage.getItem('cartItems')) || [];
    const cartContainer = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    const emptyCart = document.getElementById('empty-cart');
    const cartContent = document.getElementById('cart-content');
    
    if (cartItems.length === 0) {
        if (emptyCart) emptyCart.classList.remove('d-none');
        if (cartContent) cartContent.classList.add('d-none');
        return;
    }
    
    if (emptyCart) emptyCart.classList.add('d-none');
    if (cartContent) cartContent.classList.remove('d-none');
    
    if (cartContainer) {
        cartContainer.innerHTML = '';
        let total = 0;
        
        cartItems.forEach((item, index) => {
            const itemTotal = item.price * item.quantity;
            total += itemTotal;
            
            const itemElement = document.createElement('div');
            itemElement.className = 'cart-item row align-items-center border-bottom pb-3 mb-3';
            itemElement.innerHTML = `
                <div class="col-md-2">
                    <img src="/static/images/products/${item.image}" alt="${item.name}" class="img-fluid rounded">
                </div>
                <div class="col-md-4">
                    <h5 class="mb-1">${item.name}</h5>
                    <p class="text-muted mb-0">${item.price} ر.س</p>
                </div>
                <div class="col-md-3">
                    <div class="input-group">
                        <button class="btn btn-outline-secondary decrease-quantity" type="button" data-index="${index}">-</button>
                        <input type="number" class="form-control text-center quantity-input" value="${item.quantity}" min="1" data-index="${index}">
                        <button class="btn btn-outline-secondary increase-quantity" type="button" data-index="${index}">+</button>
                    </div>
                </div>
                <div class="col-md-2">
                    <h5 class="text-primary item-total">${itemTotal} ر.س</h5>
                </div>
                <div class="col-md-1">
                    <button class="btn btn-danger btn-sm remove-item" data-index="${index}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `;
            
            cartContainer.appendChild(itemElement);
        });
        
        if (cartTotal) {
            cartTotal.textContent = `${total} ر.س`;
        }
    }
}

// إعداد أحداث السلة
function setupCartEvents() {
    // زيادة الكمية
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('increase-quantity')) {
            const index = e.target.dataset.index;
            updateQuantity(index, 1);
        }
        
        // تقليل الكمية
        if (e.target.classList.contains('decrease-quantity')) {
            const index = e.target.dataset.index;
            updateQuantity(index, -1);
        }
        
        // إزالة العنصر
        if (e.target.classList.contains('remove-item')) {
            const index = e.target.dataset.index;
            removeItem(index);
        }
    });
    
    // تغيير الكمية يدوياً
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('quantity-input')) {
            const index = e.target.dataset.index;
            const newQuantity = parseInt(e.target.value);
            
            if (newQuantity < 1) {
                e.target.value = 1;
                return;
            }
            
            updateQuantity(index, 0, newQuantity);
        }
    });
    
    // متابعة التسوق
    const continueShopping = document.getElementById('continue-shopping');
    if (continueShopping) {
        continueShopping.addEventListener('click', function() {
            window.location.href = '/products';
        });
    }
    
    // إكمال الطلب
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function() {
            window.location.href = '/checkout';
        });
    }
}

// تحديث كمية العنصر
function updateQuantity(index, change, newQuantity = null) {
    let cartItems = JSON.parse(localStorage.getItem('cartItems')) || [];
    
    if (newQuantity !== null) {
        cartItems[index].quantity = newQuantity;
    } else {
        cartItems[index].quantity += change;
        
        if (cartItems[index].quantity < 1) {
            cartItems[index].quantity = 1;
        }
    }
    
    localStorage.setItem('cartItems', JSON.stringify(cartItems));
    loadCartItems();
    updateCartCount();
}

// إزالة العنصر من السلة
function removeItem(index) {
    let cartItems = JSON.parse(localStorage.getItem('cartItems')) || [];
    cartItems.splice(index, 1);
    localStorage.setItem('cartItems', JSON.stringify(cartItems));
    loadCartItems();
    updateCartCount();
    
    showAlert('تمت إزالة المنتج من السلة', 'success');
}

// تحديث عدد العناصر في السلة
function updateCartCount() {
    const cartItems = JSON.parse(localStorage.getItem('cartItems')) || [];
    const cartCountElements = document.querySelectorAll('.cart-count');
    
    cartCountElements.forEach(element => {
        element.textContent = cartItems.length;
    });
}

// مسح السلة بالكامل
function clearCart() {
    localStorage.removeItem('cartItems');
    loadCartItems();
    updateCartCount();
    showAlert('تم مسح سلة التسوق', 'success');
}