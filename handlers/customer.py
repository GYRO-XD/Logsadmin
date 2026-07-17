
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import db
from keyboards.customer import (
    get_main_menu_keyboard, get_categories_keyboard, get_products_keyboard,
    get_product_detail_keyboard, get_cart_keyboard, get_order_history_keyboard,
    get_support_keyboard, get_wishlist_keyboard, get_checkout_keyboard
)
from utils.helpers import generate_order_number, format_price, format_order_status
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_QUANTITY, UPLOADING_PROOF = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    
    # Save user to database
    db.add_user(
        user.id,
        user.username,
        user.first_name,
        user.last_name
    )
    
    welcome_text = (
        f"🎉 Welcome to Logs Admin Marketplace, {user.first_name}!\n\n"
        "Your one-stop shop for premium digital products.\n\n"
        "🛍 Browse our collection\n"
        "💳 Secure payments\n"
        "📦 Instant delivery after approval\n\n"
        "Use the menu below to navigate:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📍 Main Menu\nSelect an option:",
        reply_markup=get_main_menu_keyboard()
    )

async def browse_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show categories or products if no categories"""
    query = update.callback_query
    await query.answer()
    
    categories = db.get_categories()
    
    if not categories:
        # If no categories, show all products directly
        products = db.get_products()
        if not products:
            await query.edit_message_text(
                "📭 No products available yet.\nPlease check back later!",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await query.edit_message_text(
                "🛍 Available Products:",
                reply_markup=get_products_keyboard(products)
            )
    else:
        await query.edit_message_text(
            "📁 Browse Categories:",
            reply_markup=get_categories_keyboard(categories)
        )

async def show_category_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show products in a category"""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split('_')[1])
    category = db.get_category(category_id)
    products = db.get_products(category_id=category_id)
    
    if not products:
        await query.edit_message_text(
            f"📭 No products in {category['name']} yet.",
            reply_markup=get_categories_keyboard(db.get_categories())
        )
    else:
        await query.edit_message_text(
            f"📁 {category['name']}\nSelect a product:",
            reply_markup=get_products_keyboard(products, category_id=category_id)
        )

async def show_uncategorized_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show products without category"""
    query = update.callback_query
    await query.answer()
    
    products = db.get_products(category_id=None)
    
    if not products:
        await query.edit_message_text(
            "📭 No uncategorized products available.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await query.edit_message_text(
            "📦 Products Without Category:",
            reply_markup=get_products_keyboard(products)
        )

async def show_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show product details"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[1])
    product = db.get_product(product_id)
    
    if not product:
        await query.edit_message_text(
            "❌ Product not found.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Check if in wishlist
    user_id = update.effective_user.id
    wishlist = db.get_wishlist(user_id)
    is_wishlisted = any(item['product_id'] == product_id for item in wishlist)
    
    # Product details text
    stock_text = "♾️ Unlimited" if product['stock'] == -1 else str(product['stock'])
    status_text = "✅ Active" if product['is_active'] else "🔴 Inactive"
    
    detail_text = (
        f"🛍 *{product['name']}*\n\n"
        f"💰 Price: {format_price(product['price'])}\n"
        f"📦 Stock: {stock_text}\n"
        f"📂 Category: {product['category_name'] or 'None'}\n"
        f"📊 Status: {status_text}\n"
    )
    
    if product['description']:
        detail_text += f"\n📝 *Description:*\n{product['description']}\n"
    
    # Get reviews count
    reviews = db.get_product_reviews(product_id)
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
        detail_text += f"\n⭐ Rating: {avg_rating:.1f}/5 ({len(reviews)} reviews)"
    
    # Get files info
    files = db.get_product_files(product_id)
    if files:
        detail_text += f"\n\n📎 Includes {len(files)} file(s)"
    
    await query.edit_message_text(
        detail_text,
        reply_markup=get_product_detail_keyboard(product_id, is_wishlisted),
        parse_mode='Markdown'
    )

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add product to cart"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    
    product = db.get_product(product_id)
    if not product or not product['is_active']:
        await query.answer("❌ Product not available", show_alert=True)
        return
    
    db.add_to_cart(user_id, product_id)
    await query.answer("✅ Added to cart!", show_alert=True)

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View shopping cart"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    cart_items = db.get_cart(user_id)
    
    if not cart_items:
        await query.edit_message_text(
            "🛒 Your cart is empty.\nStart shopping now!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    cart_text = "🛒 *Your Shopping Cart*\n\n"
    total = 0
    
    for item in cart_items:
        subtotal = item['price'] * item['quantity']
        total += subtotal
        cart_text += f"• {item['name']} x{item['quantity']} = {format_price(subtotal)}\n"
    
    cart_text += f"\n💰 *Total: {format_price(total)}*"
    
    await query.edit_message_text(
        cart_text,
        reply_markup=get_cart_keyboard(cart_items),
        parse_mode='Markdown'
    )

async def remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove item from cart"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    
    db.remove_from_cart(user_id, product_id)
    await query.answer("🗑 Removed from cart", show_alert=True)
    
    # Refresh cart view
    await view_cart(update, context)

async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear entire cart"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db.clear_cart(user_id)
    
    await query.edit_message_text(
        "🗑 Cart cleared successfully!",
        reply_markup=get_main_menu_keyboard()
    )

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checkout process"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    cart_items = db.get_cart(user_id)
    
    if not cart_items:
        await query.edit_message_text(
            "🛒 Your cart is empty!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Calculate total
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Create order
    order_number = generate_order_number()
    order_id = db.create_order(order_number, user_id, total)
    
    # Add order items
    for item in cart_items:
        db.add_order_item(order_id, item['product_id'], item['quantity'], item['price'])
    
    # Clear cart
    db.clear_cart(user_id)
    
    # Get payment instructions
    payment_instructions = db.get_setting('payment_instructions') or "Payment instructions not configured"
    
    checkout_text = (
        f"📦 *Order Created Successfully!*\n\n"
        f"Order ID: `{order_number}`\n"
        f"Total Amount: {format_price(total)}\n\n"
        f"📋 *Payment Instructions:*\n{payment_instructions}\n\n"
        f"Please upload your payment screenshot to complete the order."
    )
    
    # Notify admins
    user = update.effective_user
    admin_notification = (
        f"🔔 *New Order Received*\n\n"
        f"Order: `{order_number}`\n"
        f"Customer: {user.first_name} (@{user.username})\n"
        f"Total: {format_price(total)}\n\n"
        f"Items:\n"
    )
    
    for item in cart_items:
        admin_notification += f"• {item['name']} x{item['quantity']}\n"
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_notification,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    await query.edit_message_text(
        checkout_text,
        reply_markup=get_checkout_keyboard(order_id),
        parse_mode='Markdown'
    )

async def upload_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment proof upload"""
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.split('_')[2])
    context.user_data['uploading_proof_for'] = order_id
    
    await query.edit_message_text(
        "📤 Please send your payment screenshot/image now.\n\n"
        "Make sure the image is clear and shows transaction details.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data=f"view_order_{order_id}")
        ]])
    )
    return UPLOADING_PROOF

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process uploaded payment proof"""
    user_id = update.effective_user.id
    order_id = context.user_data.get('uploading_proof_for')
    
    if not order_id:
        await update.message.reply_text(
            "❌ No pending order found.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Check if photo or document
    if update.message.photo:
        file = update.message.photo[-1]
    elif update.message.document:
        file = update.message.document
    else:
        await update.message.reply_text(
            "❌ Please send an image or document.",
            reply_markup=get_main_menu_keyboard()
        )
        return UPLOADING_PROOF
    
    # Save payment proof
    from utils.helpers import save_uploaded_file
    import os
    from config import PAYMENT_PROOFS_DIR
    
    file_path = os.path.join(PAYMENT_PROOFS_DIR, f"proof_{order_id}_{user_id}.jpg")
    file_obj = await file.get_file()
    await file_obj.download_to_drive(file_path)
    
    # Update order
    db.update_order_payment_proof(order_id, file_path)
    
    # Notify admins
    order = db.get_order(order_id)
    user = update.effective_user
    
    for admin_id in ADMIN_IDS:
        try:
            with open(file_path, 'rb') as f:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=f,
                    caption=(
                        f"💰 *Payment Proof Received*\n\n"
                        f"Order: `{order['order_number']}`\n"
                        f"From: {user.first_name} (@{user.username})\n"
                        f"Amount: {format_price(order['total_amount'])}"
                    ),
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Failed to send proof to admin {admin_id}: {e}")
    
    await update.message.reply_text(
        "✅ Payment proof uploaded successfully!\n"
        "Your order will be processed shortly.",
        reply_markup=get_main_menu_keyboard()
    )
    
    return ConversationHandler.END

async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel payment proof upload"""
    await update.message.reply_text(
        "❌ Upload cancelled.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END

async def view_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View order details"""
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.split('_')[2])
    order = db.get_order(order_id)
    items = db.get_order_items(order_id)
    
    if not order:
        await query.edit_message_text(
            "❌ Order not found.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    order_text = (
        f"📦 *Order Details*\n\n"
        f"Order ID: `{order['order_number']}`\n"
        f"Status: {format_order_status(order['status'])}\n"
        f"Date: {order['created_at']}\n"
        f"Total: {format_price(order['total_amount'])}\n\n"
        f"*Items:*\n"
    )
    
    for item in items:
        order_text += f"• {item['product_name']} x{item['quantity']} = {format_price(item['price'] * item['quantity'])}\n"
    
    if order['admin_notes']:
        order_text += f"\n📝 *Admin Notes:*\n{order['admin_notes']}"
    
    await query.edit_message_text(
        order_text,
        reply_markup=get_order_history_keyboard(db.get_user_orders(update.effective_user.id)),
        parse_mode='Markdown'
    )

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's orders"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    orders = db.get_user_orders(user_id)
    
    if not orders:
        await query.edit_message_text(
            "📦 You haven't placed any orders yet.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await query.edit_message_text(
        "📦 *Your Orders:*",
        reply_markup=get_order_history_keyboard(orders),
        parse_mode='Markdown'
    )

async def add_to_wishlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add product to wishlist"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    
    db.add_to_wishlist(user_id, product_id)
    await query.answer("❤️ Added to wishlist!", show_alert=True)

async def remove_from_wishlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove product from wishlist"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    
    db.remove_from_wishlist(user_id, product_id)
    await query.answer("💔 Removed from wishlist", show_alert=True)

async def view_wishlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View wishlist"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    wishlist_items = db.get_wishlist(user_id)
    
    if not wishlist_items:
        await query.edit_message_text(
            "❤️ Your wishlist is empty.\nBrowse products to add some!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    wishlist_text = "❤️ *Your Wishlist*\n\n"
    for item in wishlist_items:
        wishlist_text += f"• {item['name']} - {format_price(item['price'])}\n"
    
    await query.edit_message_text(
        wishlist_text,
        reply_markup=get_wishlist_keyboard(wishlist_items),
        parse_mode='Markdown'
    )

async def search_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search products prompt"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔍 Please send the product name or keyword you want to search for:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Cancel", callback_data="main_menu")
        ]])
    )
    context.user_data['expecting_search'] = True

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product search"""
    if not context.user_data.get('expecting_search'):
        return
    
    search_query = update.message.text
    context.user_data['expecting_search'] = False
    
    products = db.search_products(search_query)
    
    if not products:
        await update.message.reply_text(
            f"🔍 No products found for '{search_query}'.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await update.message.reply_text(
        f"🔍 Search results for '{search_query}':",
        reply_markup=get_products_keyboard(products)
    )

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show support information"""
    query = update.callback_query
    await query.answer()
    
    support_info = db.get_setting('support_info') or "Support information not configured"
    
    await query.edit_message_text(
        f"📞 *Contact Support*\n\n{support_info}",
        reply_markup=get_support_keyboard(),
        parse_mode='Markdown'
    )

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db_user = db.get_user(user.id)
    orders = db.get_user_orders(user.id)
    
    profile_text = (
        f"👤 *Your Profile*\n\n"
        f"Name: {user.first_name} {user.last_name or ''}\n"
        f"Username: @{user.username or 'N/A'}\n"
        f"User ID: `{user.id}`\n"
        f"Joined: {db_user['joined_date'] if db_user else 'Today'}\n"
        f"Total Orders: {len(orders)}\n"
    )
    
    await query.edit_message_text(
        profile_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def buy_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buy product immediately"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    context.user_data['buy_product_id'] = product_id
    
    await query.edit_message_text(
        "📊 Please enter the quantity you want to purchase:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data=f"product_{product_id}")
        ]])
    )
    return SELECTING_QUANTITY

async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quantity input for buy now"""
    try:
        quantity = int(update.message.text)
        if quantity < 1:
            raise ValueError
    except:
        await update.message.reply_text(
            "❌ Please enter a valid number (minimum 1).",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="main_menu")
            ]])
        )
        return SELECTING_QUANTITY
    
    product_id = context.user_data.get('buy_product_id')
    if not product_id:
        await update.message.reply_text(
            "❌ Session expired. Please try again.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    product = db.get_product(product_id)
    if not product:
        await update.message.reply_text(
            "❌ Product not found.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Check stock
    if product['stock'] != -1 and quantity > product['stock']:
        await update.message.reply_text(
            f"❌ Insufficient stock. Available: {product['stock']}",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # Create order directly
    user_id = update.effective_user.id
    total = product['price'] * quantity
    order_number = generate_order_number()
    order_id = db.create_order(order_number, user_id, total)
    db.add_order_item(order_id, product_id, quantity, product['price'])
    
    # Get payment instructions
    payment_instructions = db.get_setting('payment_instructions') or "Payment instructions not configured"
    
    order_text = (
        f"📦 *Order Created Successfully!*\n\n"
        f"Order ID: `{order_number}`\n"
        f"Product: {product['name']}\n"
        f"Quantity: {quantity}\n"
        f"Total: {format_price(total)}\n\n"
        f"📋 *Payment Instructions:*\n{payment_instructions}\n\n"
        f"Please upload your payment screenshot."
    )
    
    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🔔 *New Order Received*\n\n"
                    f"Order: `{order_number}`\n"
                    f"Customer: {update.effective_user.first_name}\n"
                    f"Product: {product['name']}\n"
                    f"Quantity: {quantity}\n"
                    f"Total: {format_price(total)}"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
    
    context.user_data['uploading_proof_for'] = order_id
    
    await update.message.reply_text(
        order_text,
        reply_markup=get_checkout_keyboard(order_id),
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END
