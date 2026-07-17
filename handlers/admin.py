import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import db
from keyboards.admin import (
    get_admin_main_keyboard, get_admin_products_keyboard, get_admin_categories_keyboard,
    get_admin_orders_keyboard, get_admin_settings_keyboard, get_admin_users_keyboard,
    get_admin_stats_keyboard, get_admin_product_edit_keyboard, get_confirmation_keyboard,
    get_back_to_admin_keyboard
)
from keyboards.customer import get_products_keyboard
from utils.helpers import format_price, truncate_text

logger = logging.getLogger(__name__)

# Conversation states
ADDING_PRODUCT, EDITING_PRODUCT, ADDING_CATEGORY, BROADCASTING = range(4)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel entry point"""
    from config import ADMIN_IDS
    
    if update.effective_user.id not in ADMIN_IDS:
        if update.callback_query:
            await update.callback_query.answer("❌ Unauthorized", show_alert=True)
        else:
            await update.message.reply_text("❌ You don't have admin access.")
        return
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🔐 *Admin Panel*\n\nSelect a section to manage:",
            reply_markup=get_admin_main_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🔐 *Admin Panel*\n\nSelect a section to manage:",
            reply_markup=get_admin_main_keyboard(),
            parse_mode='Markdown'
        )

# Product Management
async def admin_products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Products management menu"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📦 *Product Management*\nSelect an action:",
        reply_markup=get_admin_products_keyboard(),
        parse_mode='Markdown'
    )

async def admin_list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all products"""
    query = update.callback_query
    await query.answer()
    
    products = db.get_products(active_only=False)
    
    if not products:
        await query.edit_message_text(
            "📦 No products yet.\nUse 'Add Product' to create one.",
            reply_markup=get_admin_products_keyboard()
        )
        return
    
    keyboard = []
    for product in products[:20]:
        status = "✅" if product['is_active'] else "🔴"
        feature = "⭐" if product['is_featured'] else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{status}{feature} {truncate_text(product['name'], 30)} - {format_price(product['price'])}",
                callback_data=f"admin_edit_product_{product['product_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_products")])
    
    await query.edit_message_text(
        "📦 *All Products*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def admin_add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add product process"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['adding_product'] = {}
    
    await query.edit_message_text(
        "📝 Let's add a new product.\n\n"
        "First, send me the product name:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="admin_products")
        ]])
    )
    return ADDING_PRODUCT

async def admin_add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product name"""
    context.user_data['adding_product']['name'] = update.message.text
    
    # Show categories
    categories = db.get_categories()
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(
            f"📁 {category['name']}",
            callback_data=f"set_cat_{category['category_id']}"
        )])
    keyboard.append([InlineKeyboardButton("⏭ Skip (No Category)", callback_data="set_cat_none")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="admin_products")])
    
    await update.message.reply_text(
        f"✅ Product name: {update.message.text}\n\n"
        "Now select a category (or skip):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADDING_PRODUCT

async def admin_add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product category"""
    query = update.callback_query
    await query.answer()
    
    cat_data = query.data.split('_')[2]
    if cat_data == 'none':
        context.user_data['adding_product']['category_id'] = None
    else:
        context.user_data['adding_product']['category_id'] = int(cat_data)
    
    await query.edit_message_text(
        "📝 Now send me the product description:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ Skip", callback_data="skip_desc")
        ]])
    )
    return ADDING_PRODUCT

async def admin_add_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product description"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        context.user_data['adding_product']['description'] = ''
        await query.edit_message_text(
            "💰 Send me the product price (numbers only):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_products")
            ]])
        )
    else:
        context.user_data['adding_product']['description'] = update.message.text
        await update.message.reply_text(
            f"✅ Description received.\n\n"
            "💰 Now send me the product price (numbers only):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_products")
            ]])
        )
    return ADDING_PRODUCT

async def admin_add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product price"""
    try:
        price = float(update.message.text)
        if price <= 0:
            raise ValueError
    except:
        await update.message.reply_text(
            "❌ Invalid price. Please enter a valid number:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="admin_products")
            ]])
        )
        return ADDING_PRODUCT
    
    context.user_data['adding_product']['price'] = price
    
    await update.message.reply_text(
        f"✅ Price set to: {format_price(price)}\n\n"
        "📦 Send me the stock quantity (-1 for unlimited):",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("♾️ Unlimited", callback_data="set_stock_unlimited")
        ]])
    )
    return ADDING_PRODUCT

async def admin_add_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product stock"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        stock = -1
        await query.edit_message_text(
            f"✅ Stock: Unlimited\n\n"
            "Now send me the product files (documents/zip/etc).\n"
            "Send /done when finished."
        )
    else:
        try:
            stock = int(update.message.text)
        except:
            await update.message.reply_text(
                "❌ Invalid number. Enter stock quantity or use button:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("♾️ Unlimited", callback_data="set_stock_unlimited")
                ]])
            )
            return ADDING_PRODUCT
        
        await update.message.reply_text(
            f"✅ Stock set to: {stock}\n\n"
            "Now send me the product files (documents/zip/etc).\n"
            "Send /done when finished."
        )
    
    context.user_data['adding_product']['stock'] = stock
    context.user_data['adding_product']['files'] = []
    context.user_data['expecting_files'] = True
    return ADDING_PRODUCT

async def admin_receive_product_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive product file"""
    if update.message.text and update.message.text == '/done':
        # Create product
        data = context.user_data['adding_product']
        product_id = db.add_product(
            name=data['name'],
            description=data.get('description', ''),
            price=data['price'],
            category_id=data.get('category_id'),
            stock=data.get('stock', -1)
        )
        
        # Save files
        files_saved = 0
        for file_path in data.get('files', []):
            file_name = os.path.basename(file_path)
            db.add_product_file(product_id, file_name, file_path, 'document')
            files_saved += 1
        
        context.user_data['expecting_files'] = False
        
        await update.message.reply_text(
            f"✅ Product created successfully!\n\n"
            f"Name: {data['name']}\n"
            f"Price: {format_price(data['price'])}\n"
            f"Files: {files_saved}\n"
            f"ID: {product_id}",
            reply_markup=get_admin_products_keyboard()
        )
        return ConversationHandler.END
    
    if update.message.document:
        file = update.message.document
        from utils.helpers import save_uploaded_file
        from config import UPLOAD_DIR
        
        file_path = os.path.join(UPLOAD_DIR, f"product_{datetime.now().timestamp()}_{file.file_name}")
        file_obj = await file.get_file()
        await file_obj.download_to_drive(file_path)
        
        context.user_data['adding_product']['files'].append(file_path)
        await update.message.reply_text(
            f"✅ File received: {file.file_name}\n"
            f"Send more files or /done to finish."
        )
    else:
        await update.message.reply_text(
            "Please send files as documents or send /done to finish."
        )
    
    return ADDING_PRODUCT

async def admin_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit product menu"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[3])
    product = db.get_product(product_id)
    
    if not product:
        await query.edit_message_text(
            "❌ Product not found",
            reply_markup=get_admin_products_keyboard()
        )
        return
    
    product_text = (
        f"📦 *Edit Product*\n\n"
        f"Name: {product['name']}\n"
        f"Price: {format_price(product['price'])}\n"
        f"Stock: {'Unlimited' if product['stock'] == -1 else product['stock']}\n"
        f"Status: {'✅ Active' if product['is_active'] else '🔴 Inactive'}\n"
        f"Featured: {'⭐ Yes' if product['is_featured'] else '❌ No'}"
    )
    
    context.user_data['editing_product_id'] = product_id
    
    await query.edit_message_text(
        product_text,
        reply_markup=get_admin_product_edit_keyboard(product_id),
        parse_mode='Markdown'
    )

async def admin_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete product with confirmation"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    
    await query.edit_message_text(
        "⚠️ Are you sure you want to delete this product?",
        reply_markup=get_confirmation_keyboard('delete_product', product_id)
    )

async def admin_confirm_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and execute product deletion"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[3])
    db.delete_product(product_id)
    
    await query.edit_message_text(
        "✅ Product deleted successfully!",
        reply_markup=get_admin_products_keyboard()
    )

async def admin_toggle_product_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle product active/inactive"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    product = db.get_product(product_id)
    new_status = 0 if product['is_active'] else 1
    
    db.update_product(product_id, is_active=new_status)
    status_text = "activated" if new_status else "deactivated"
    
    await query.answer(f"Product {status_text}!", show_alert=True)
    await admin_edit_product(update, context)

async def admin_toggle_product_featured(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle product featured status"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    product = db.get_product(product_id)
    new_status = 0 if product['is_featured'] else 1
    
    db.update_product(product_id, is_featured=new_status)
    status_text = "featured" if new_status else "unfeatured"
    
    await query.answer(f"Product {status_text}!", show_alert=True)
    await admin_edit_product(update, context)

async def admin_edit_product_field_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing a product field"""
    query = update.callback_query
    await query.answer()
    
    field_map = {
        'name': 'edit_name',
        'desc': 'edit_desc',
        'price': 'edit_price',
        'stock': 'edit_stock'
    }
    
    product_id = int(query.data.split('_')[2])
    field = None
    
    for key, value in field_map.items():
        if value in query.data:
            field = key
            break
    
    context.user_data['editing_field'] = field
    context.user_data['editing_product_id'] = product_id
    
    prompts = {
        'name': 'Send the new product name:',
        'desc': 'Send the new product description:',
        'price': 'Send the new price (numbers only):',
        'stock': 'Send the new stock quantity (-1 for unlimited):'
    }
    
    await query.edit_message_text(
        prompts.get(field, 'Send the new value:'),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data=f"admin_edit_product_{product_id}")
        ]])
    )
    return EDITING_PRODUCT

async def admin_receive_edited_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive edited field value"""
    field = context.user_data.get('editing_field')
    product_id = context.user_data.get('editing_product_id')
    
    if not field or not product_id:
        await update.message.reply_text(
            "❌ Session expired",
            reply_markup=get_admin_main_keyboard()
        )
        return ConversationHandler.END
    
    if field == 'price':
        try:
            value = float(update.message.text)
        except:
            await update.message.reply_text("❌ Invalid price. Try again:")
            return EDITING_PRODUCT
    elif field == 'stock':
        try:
            value = int(update.message.text)
        except:
            await update.message.reply_text("❌ Invalid number. Try again:")
            return EDITING_PRODUCT
    else:
        value = update.message.text
    
    db.update_product(product_id, **{field: value})
    
    await update.message.reply_text(
        f"✅ Product updated successfully!",
        reply_markup=get_admin_main_keyboard()
    )
    
    # Show updated product
    await update.message.reply_text(
        "Updated product details:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "View Product",
                callback_data=f"admin_edit_product_{product_id}"
            )
        ]])
    )
    
    return ConversationHandler.END

# Category Management
async def admin_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Categories management menu"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📁 *Category Management*\nSelect an action:",
        reply_markup=get_admin_categories_keyboard(),
        parse_mode='Markdown'
    )

async def admin_list_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all categories"""
    query = update.callback_query
    await query.answer()
    
    categories = db.get_categories()
    
    if not categories:
        await query.edit_message_text(
            "📁 No categories yet.\nUse 'Add Category' to create one.",
            reply_markup=get_admin_categories_keyboard()
        )
        return
    
    keyboard = []
    for cat in categories:
        product_count = len(db.get_products(category_id=cat['category_id']))
        keyboard.append([
            InlineKeyboardButton(
                f"📁 {cat['name']} ({product_count} products)",
                callback_data=f"edit_category_{cat['category_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_categories")])
    
    await query.edit_message_text(
        "📁 *Categories*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def admin_add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add category process"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📝 Send the category name:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="admin_categories")
        ]])
    )
    return ADDING_CATEGORY

async def admin_add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive category name"""
    name = update.message.text
    context.user_data['category_name'] = name
    
    await update.message.reply_text(
        f"✅ Name: {name}\n\nSend the category description (or /skip):"
    )
    return ADDING_CATEGORY

async def admin_add_category_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive category description and create"""
    if update.message.text == '/skip':
        description = ''
    else:
        description = update.message.text
    
    name = context.user_data.get('category_name', 'Unnamed')
    category_id = db.add_category(name, description)
    
    await update.message.reply_text(
        f"✅ Category '{name}' created successfully!\nID: {category_id}",
        reply_markup=get_admin_categories_keyboard()
    )
    return ConversationHandler.END

# User Management
async def admin_users_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Users management menu"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👥 *User Management*\nSelect an action:",
        reply_markup=get_admin_users_keyboard(),
        parse_mode='Markdown'
    )

async def admin_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users"""
    query = update.callback_query
    await query.answer()
    
    users = db.get_all_users()
    
    if not users:
        await query.edit_message_text(
            "👥 No users yet.",
            reply_markup=get_admin_users_keyboard()
        )
        return
    
    users_text = "👥 *All Users*\n\n"
    for user in users[:20]:
        users_text += f"• {user['first_name']} (@{user['username'] or 'N/A'}) - ID: `{user['user_id']}`\n"
    
    users_text += f"\nTotal: {len(users)} users"
    
    await query.edit_message_text(
        users_text,
        reply_markup=get_admin_users_keyboard(),
        parse_mode='Markdown'
    )

# Broadcast
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast message"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📢 Send the message you want to broadcast to all users:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="admin_main")
        ]])
    )
    return BROADCASTING

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send broadcast message to all users"""
    message = update.message.text
    users = db.get_all_users()
    
    success = 0
    failed = 0
    
    await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 *Broadcast Message*\n\n{message}",
                parse_mode='Markdown'
            )
            success += 1
        except Exception as e:
            logger.error(f"Failed to send to {user['user_id']}: {e}")
            failed += 1
    
    db.log_broadcast(update.effective_user.id, message, success)
    
    await update.message.reply_text(
        f"✅ Broadcast complete!\n\n"
        f"Sent: {success}\n"
        f"Failed: {failed}",
        reply_markup=get_admin_main_keyboard()
    )
    return ConversationHandler.END

# Statistics
async def admin_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics menu"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📊 *Statistics*\nSelect a report:",
        reply_markup=get_admin_stats_keyboard(),
        parse_mode='Markdown'
    )

async def admin_sales_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show sales statistics"""
    query = update.callback_query
    await query.answer()
    
    stats = db.get_sales_stats()
    
    stats_text = (
        f"📊 *Sales Overview*\n\n"
        f"✅ Completed Orders: {stats['completed_orders']}\n"
        f"⏳ Pending Orders: {stats['pending_orders']}\n"
        f"💰 Total Revenue: {format_price(stats['total_revenue'])}\n"
        f"👥 Total Customers: {stats['total_customers']}\n"
    )
    
    await query.edit_message_text(
        stats_text,
        reply_markup=get_admin_stats_keyboard(),
        parse_mode='Markdown'
    )

async def admin_top_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top selling products"""
    query = update.callback_query
    await query.answer()
    
    products = db.get_top_products(10)
    
    if not products:
        await query.edit_message_text(
            "📊 No sales data yet.",
            reply_markup=get_admin_stats_keyboard()
        )
        return
    
    text = "🏆 *Top Selling Products*\n\n"
    for i, product in enumerate(products, 1):
        text += f"{i}. {product['name']} - {product['order_count']} sales - {format_price(product['revenue'])}\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_admin_stats_keyboard(),
        parse_mode='Markdown'
    )

# Settings
async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Settings menu"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⚙️ *Settings*\nSelect a setting to edit:",
        reply_markup=get_admin_settings_keyboard(),
        parse_mode='Markdown'
    )

async def admin_edit_payment_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit payment instructions"""
    query = update.callback_query
    await query.answer()
    
    current = db.get_setting('payment_instructions')
    
    await query.edit_message_text(
        f"💳 Current payment instructions:\n\n{current}\n\n"
        "Send new payment instructions:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")
        ]])
    )
    context.user_data['editing_setting'] = 'payment_instructions'
    return EDITING_PRODUCT

async def admin_edit_support_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit support information"""
    query = update.callback_query
    await query.answer()
    
    current = db.get_setting('support_info')
    
    await query.edit_message_text(
        f"📞 Current support info:\n\n{current}\n\n"
        "Send new support information:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")
        ]])
    )
    context.user_data['editing_setting'] = 'support_info'
    return EDITING_PRODUCT

async def admin_receive_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new setting value"""
    setting_key = context.user_data.get('editing_setting')
    
    if not setting_key:
        return ConversationHandler.END
    
    db.update_setting(setting_key, update.message.text)
    
    await update.message.reply_text(
        "✅ Setting updated successfully!",
        reply_markup=get_admin_main_keyboard()
    )
    return ConversationHandler.END

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ Operation cancelled.",
            reply_markup=get_admin_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Operation cancelled.",
            reply_markup=get_admin_main_keyboard()
        )
    return ConversationHandler.END

async def manage_product_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage product files"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    product = db.get_product(product_id)
    files = db.get_product_files(product_id)
    
    if not files:
        file_text = "No files attached to this product."
    else:
        file_text = "📎 *Product Files:*\n\n"
        for i, file in enumerate(files, 1):
            file_text += f"{i}. {file['file_name']}\n"
    
    keyboard = [
        [InlineKeyboardButton("📤 Upload New File", callback_data=f"upload_file_{product_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"admin_edit_product_{product_id}")]
    ]
    
    # Add delete buttons for each file
    for file in files[:10]:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑 Delete: {file['file_name'][:30]}",
                callback_data=f"delete_file_{file['file_id']}_{product_id}"
            )
        ])
    
    await query.edit_message_text(
        file_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def upload_product_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upload new file to product"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[2])
    context.user_data['uploading_to_product'] = product_id
    context.user_data['expecting_product_file'] = True
    
    await query.edit_message_text(
        "📤 Send me the file(s) you want to add to this product.\n"
        "Send /done when finished.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data=f"admin_edit_product_{product_id}")
        ]])
    )

async def handle_product_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file upload for product"""
    if not context.user_data.get('expecting_product_file'):
        return
    
    product_id = context.user_data.get('uploading_to_product')
    
    if update.message.text == '/done':
        context.user_data['expecting_product_file'] = False
        await update.message.reply_text(
            "✅ Files uploaded successfully!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("View Product", callback_data=f"admin_edit_product_{product_id}")
            ]])
        )
        return ConversationHandler.END
    
    if update.message.document:
        from config import UPLOAD_DIR
        file = update.message.document
        file_name = file.file_name
        file_path = os.path.join(UPLOAD_DIR, f"product_{product_id}_{datetime.now().timestamp()}_{file_name}")
        
        file_obj = await file.get_file()
        await file_obj.download_to_drive(file_path)
        
        db.add_product_file(product_id, file_name, file_path, 'document')
        
        await update.message.reply_text(
            f"✅ File added: {file_name}\nSend more or /done to finish."
        )
    else:
        await update.message.reply_text("Please send files as documents.")
    
    return ADDING_PRODUCT

async def delete_product_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a product file"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    file_id = int(parts[2])
    product_id = int(parts[3])
    
    db.delete_product_file(file_id)
    
    await query.answer("File deleted!", show_alert=True)
    await manage_product_files(update, context)

async def handle_search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user search"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔍 Send me the username or name to search:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="admin_users")
        ]])
    )
    context.user_data['searching_user'] = True

async def handle_user_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process user search result"""
    if not context.user_data.get('searching_user'):
        return
    
    query = update.message.text
    context.user_data['searching_user'] = False
    
    users = db.search_users(query)
    
    if not users:
        await update.message.reply_text(
            f"🔍 No users found for '{query}'.",
            reply_markup=get_admin_users_keyboard()
        )
        return
    
    text = f"🔍 Search results for '{query}':\n\n"
    for user in users[:20]:
        text += f"• {user['first_name']} (@{user['username'] or 'N/A'}) - ID: `{user['user_id']}`\n"
    
    await update.message.reply_text(
        text,
        reply_markup=get_admin_users_keyboard(),
        parse_mode='Markdown'
    )
