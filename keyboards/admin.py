
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ITEMS_PER_PAGE

def get_admin_main_keyboard():
    """Admin main menu"""
    keyboard = [
        [InlineKeyboardButton("📦 Products", callback_data="admin_products")],
        [InlineKeyboardButton("📁 Categories", callback_data="admin_categories")],
        [
            InlineKeyboardButton("📋 Orders", callback_data="admin_orders"),
            InlineKeyboardButton("💰 Payments", callback_data="admin_payments")
        ],
        [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ],
        [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("🏠 Customer Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_products_keyboard(page=1):
    """Admin products management"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Product", callback_data="admin_add_product"),
            InlineKeyboardButton("📋 List Products", callback_data="admin_list_products")
        ],
        [
            InlineKeyboardButton("⭐ Featured", callback_data="admin_featured_products"),
            InlineKeyboardButton("🔍 Search", callback_data="admin_search_product")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_categories_keyboard(page=1):
    """Admin categories management"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Category", callback_data="admin_add_category"),
            InlineKeyboardButton("📋 List Categories", callback_data="admin_list_categories")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_orders_keyboard():
    """Admin orders management"""
    keyboard = [
        [InlineKeyboardButton("📋 All Orders", callback_data="admin_all_orders")],
        [
            InlineKeyboardButton("⏳ Pending", callback_data="admin_pending_orders"),
            InlineKeyboardButton("✅ Completed", callback_data="admin_completed_orders")
        ],
        [InlineKeyboardButton("❌ Rejected", callback_data="admin_rejected_orders")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_order_detail_keyboard(order_id, status):
    """Admin order detail with actions"""
    keyboard = []
    
    if status == 'pending':
        keyboard.append([
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_order_{order_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_order_{order_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Orders", callback_data="admin_orders")])
    
    return InlineKeyboardMarkup(keyboard)

def get_admin_product_edit_keyboard(product_id):
    """Admin product edit options"""
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Name", callback_data=f"edit_name_{product_id}")],
        [InlineKeyboardButton("📝 Edit Description", callback_data=f"edit_desc_{product_id}")],
        [InlineKeyboardButton("💵 Edit Price", callback_data=f"edit_price_{product_id}")],
        [InlineKeyboardButton("📊 Edit Stock", callback_data=f"edit_stock_{product_id}")],
        [InlineKeyboardButton("📁 Manage Files", callback_data=f"manage_files_{product_id}")],
        [InlineKeyboardButton("📂 Set Category", callback_data=f"set_category_{product_id}")],
        [
            InlineKeyboardButton("⭐ Toggle Featured", callback_data=f"toggle_featured_{product_id}"),
            InlineKeyboardButton("🔴 Toggle Active", callback_data=f"toggle_active_{product_id}")
        ],
        [InlineKeyboardButton("🗑 Delete Product", callback_data=f"delete_product_{product_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_products")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_settings_keyboard():
    """Admin settings menu"""
    keyboard = [
        [InlineKeyboardButton("💳 Payment Instructions", callback_data="edit_payment_instructions")],
        [InlineKeyboardButton("📞 Support Info", callback_data="edit_support_info")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_users_keyboard(page=1):
    """Admin users management"""
    keyboard = [
        [
            InlineKeyboardButton("👥 All Users", callback_data="admin_all_users"),
            InlineKeyboardButton("🔍 Search", callback_data="admin_search_user")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_stats_keyboard():
    """Admin statistics menu"""
    keyboard = [
        [InlineKeyboardButton("📊 Sales Overview", callback_data="stats_sales")],
        [InlineKeyboardButton("🏆 Top Products", callback_data="stats_top_products")],
        [InlineKeyboardButton("📈 Export Data", callback_data="stats_export")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action, item_id):
    """Generic confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"cancel_{action}_{item_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_admin_keyboard():
    """Simple back button to admin menu"""
    keyboard = [[InlineKeyboardButton("🔙 Back to Admin Menu", callback_data="admin_main")]]
    return InlineKeyboardMarkup(keyboard)
