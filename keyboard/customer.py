from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ITEMS_PER_PAGE

def get_main_menu_keyboard():
    """Main customer menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🛍 Browse Products", callback_data="browse_products")],
        [
            InlineKeyboardButton("🔍 Search", callback_data="search_products"),
            InlineKeyboardButton("🛒 Cart", callback_data="view_cart")
        ],
        [
            InlineKeyboardButton("❤️ Wishlist", callback_data="view_wishlist"),
            InlineKeyboardButton("📦 My Orders", callback_data="my_orders")
        ],
        [InlineKeyboardButton("📞 Support", callback_data="support")],
        [InlineKeyboardButton("👤 My Profile", callback_data="my_profile")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_categories_keyboard(categories, page=1):
    """Categories listing with pagination"""
    from utils.helpers import paginate_list
    
    items, total_pages, current_page = paginate_list(categories, page, ITEMS_PER_PAGE)
    
    keyboard = []
    for category in items:
        keyboard.append([
            InlineKeyboardButton(
                f"📁 {category['name']}",
                callback_data=f"category_{category['category_id']}"
            )
        ])
    
    # Pagination row
    if total_pages > 1:
        nav_row = []
        if current_page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"cat_page_{current_page-1}"))
        nav_row.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="ignore"))
        if current_page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"cat_page_{current_page+1}"))
        keyboard.append(nav_row)
    
    # Also show uncategorized products option
    keyboard.append([InlineKeyboardButton("📦 Products Without Category", callback_data="uncategorized_products")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_products_keyboard(products, page=1, category_id=None):
    """Products listing with pagination"""
    from utils.helpers import paginate_list
    
    items, total_pages, current_page = paginate_list(products, page, ITEMS_PER_PAGE)
    
    keyboard = []
    for product in items:
        stock_status = ""
        if product['stock'] == 0:
            stock_status = " 🔴"
        elif product['stock'] > 0:
            stock_status = f" ({product['stock']} left)"
        else:
            stock_status = " ♾️"
            
        keyboard.append([
            InlineKeyboardButton(
                f"🛍 {product['name']} - ₦{product['price']:,.2f}{stock_status}",
                callback_data=f"product_{product['product_id']}"
            )
        ])
    
    # Pagination row
    if total_pages > 1:
        nav_row = []
        if current_page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"prod_page_{page-1}_{category_id or 'all'}"))
        nav_row.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="ignore"))
        if current_page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"prod_page_{page+1}_{category_id or 'all'}"))
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="browse_products" if category_id else "main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_product_detail_keyboard(product_id, is_wishlisted=False):
    """Product detail view keyboard"""
    keyboard = [
        [InlineKeyboardButton("🛒 Add to Cart", callback_data=f"add_cart_{product_id}")],
        [InlineKeyboardButton("🛍 Buy Now", callback_data=f"buy_now_{product_id}")],
    ]
    
    wishlist_text = "💔 Remove from Wishlist" if is_wishlisted else "❤️ Add to Wishlist"
    wishlist_callback = f"remove_wishlist_{product_id}" if is_wishlisted else f"add_wishlist_{product_id}"
    
    keyboard.append([InlineKeyboardButton(wishlist_text, callback_data=wishlist_callback)])
    keyboard.append([InlineKeyboardButton("⭐ Reviews", callback_data=f"reviews_{product_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="browse_products")])
    
    return InlineKeyboardMarkup(keyboard)

def get_cart_keyboard(cart_items):
    """Shopping cart keyboard"""
    keyboard = []
    total = 0
    
    for item in cart_items:
        total += item['price'] * item['quantity']
        keyboard.append([
            InlineKeyboardButton(
                f"❌ {item['name']} x{item['quantity']}",
                callback_data=f"remove_cart_{item['product_id']}"
            )
        ])
    
    if cart_items:
        keyboard.append([InlineKeyboardButton(f"💳 Checkout (₦{total:,.2f})", callback_data="checkout")])
        keyboard.append([InlineKeyboardButton("🗑 Clear Cart", callback_data="clear_cart")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_order_history_keyboard(orders, page=1):
    """Order history with pagination"""
    from utils.helpers import paginate_list, format_order_status
    
    items, total_pages, current_page = paginate_list(orders, page, ITEMS_PER_PAGE)
    
    keyboard = []
    for order in items:
        keyboard.append([
            InlineKeyboardButton(
                f"📦 {order['order_number']} - {format_order_status(order['status'])}",
                callback_data=f"order_detail_{order['order_id']}"
            )
        ])
    
    if total_pages > 1:
        nav_row = []
        if current_page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"order_page_{current_page-1}"))
        nav_row.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="ignore"))
        if current_page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"order_page_{current_page+1}"))
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_support_keyboard():
    """Support contact keyboard"""
    from config import SUPPORT_TELEGRAM, SUPPORT_WHATSAPP
    
    keyboard = [
        [InlineKeyboardButton("📱 Telegram Support", url=f"https://t.me/{SUPPORT_TELEGRAM.replace('@', '')}")],
        [InlineKeyboardButton("💬 WhatsApp Support", url=SUPPORT_WHATSAPP)],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_wishlist_keyboard(wishlist_items):
    """Wishlist keyboard"""
    keyboard = []
    
    for item in wishlist_items:
        keyboard.append([
            InlineKeyboardButton(
                f"🛍 {item['name']} - ₦{item['price']:,.2f}",
                callback_data=f"product_{item['product_id']}"
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=f"remove_wishlist_{item['product_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def get_checkout_keyboard(order_id):
    """Checkout and payment keyboard"""
    keyboard = [
        [InlineKeyboardButton("📤 Upload Payment Proof", callback_data=f"upload_proof_{order_id}")],
        [InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{order_id}")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
