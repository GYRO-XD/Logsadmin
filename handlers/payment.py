
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from keyboards.admin import get_back_to_admin_keyboard
from keyboards.customer import get_main_menu_keyboard
from utils.helpers import format_price, format_order_status
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve order and deliver files"""
    query = update.callback_query
    await query.answer()
    
    # Check if admin
    if update.effective_user.id not in ADMIN_IDS:
        await query.answer("❌ Unauthorized", show_alert=True)
        return
    
    order_id = int(query.data.split('_')[2])
    order = db.get_order(order_id)
    
    if not order:
        await query.answer("❌ Order not found", show_alert=True)
        return
    
    if order['status'] != 'pending':
        await query.answer(f"Order is already {order['status']}", show_alert=True)
        return
    
    # Update order status
    db.update_order_status(order_id, 'approved')
    
    # Get order items
    items = db.get_order_items(order_id)
    
    # Deliver files to customer
    user_id = order['user_id']
    delivered_files = []
    
    for item in items:
        files = db.get_product_files(item['product_id'])
        for file in files:
            try:
                if os.path.exists(file['file_path']):
                    with open(file['file_path'], 'rb') as f:
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=f,
                            caption=f"📦 Order: {order['order_number']}\nProduct: {item['product_name']}\nFile: {file['file_name']}"
                        )
                    delivered_files.append(file['file_name'])
                else:
                    logger.error(f"File not found: {file['file_path']}")
            except Exception as e:
                logger.error(f"Failed to deliver file {file['file_name']}: {e}")
    
    # Notify customer
    delivery_message = (
        f"✅ *Payment Approved!*\n\n"
        f"Order: `{order['order_number']}`\n"
        f"Your digital products have been delivered above.\n\n"
        f"Thank you for your purchase! 🎉"
    )
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=delivery_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to notify customer {user_id}: {e}")
    
    # Update order to completed
    db.update_order_status(order_id, 'completed')
    
    # Update admin message
    await query.edit_message_text(
        f"✅ Order {order['order_number']} approved and files delivered!\n"
        f"Files delivered: {len(delivered_files)}",
        reply_markup=get_back_to_admin_keyboard()
    )

async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reject order"""
    query = update.callback_query
    await query.answer()
    
    # Check if admin
    if update.effective_user.id not in ADMIN_IDS:
        await query.answer("❌ Unauthorized", show_alert=True)
        return
    
    order_id = int(query.data.split('_')[2])
    order = db.get_order(order_id)
    
    if not order:
        await query.answer("❌ Order not found", show_alert=True)
        return
    
    if order['status'] != 'pending':
        await query.answer(f"Order is already {order['status']}", show_alert=True)
        return
    
    # Update order status
    db.update_order_status(order_id, 'rejected', 'Payment rejected by admin')
    
    # Notify customer
    try:
        await context.bot.send_message(
            chat_id=order['user_id'],
            text=(
                f"❌ *Payment Rejected*\n\n"
                f"Order: `{order['order_number']}`\n"
                f"Unfortunately, your payment could not be verified.\n"
                f"Please contact support if you believe this is an error."
            ),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to notify customer: {e}")
    
    await query.edit_message_text(
        f"❌ Order {order['order_number']} rejected.",
        reply_markup=get_back_to_admin_keyboard()
    )

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel order (customer)"""
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.split('_')[2])
    order = db.get_order(order_id)
    
    if not order:
        await query.answer("❌ Order not found", show_alert=True)
        return
    
    if order['user_id'] != update.effective_user.id:
        await query.answer("❌ Unauthorized", show_alert=True)
        return
    
    if order['status'] != 'pending':
        await query.answer("Cannot cancel this order", show_alert=True)
        return
    
    db.update_order_status(order_id, 'cancelled')
    
    await query.edit_message_text(
        f"🚫 Order {order['order_number']} cancelled.",
        reply_markup=get_main_menu_keyboard()
    )

async def admin_view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin view orders by status"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id not in ADMIN_IDS:
        await query.answer("❌ Unauthorized", show_alert=True)
        return
    
    action = query.data
    
    if action == "admin_all_orders":
        orders = db.get_all_orders()
        title = "📋 All Orders"
    elif action == "admin_pending_orders":
        orders = db.get_all_orders(status='pending')
        title = "⏳ Pending Orders"
    elif action == "admin_completed_orders":
        orders = db.get_all_orders(status='completed')
        title = "✅ Completed Orders"
    elif action == "admin_rejected_orders":
        orders = db.get_all_orders(status='rejected')
        title = "❌ Rejected Orders"
    else:
        orders = db.get_all_orders()
        title = "📋 Orders"
    
    if not orders:
        await query.edit_message_text(
            f"{title}\n\nNo orders found.",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    # Build message
    message = f"{title}\n\n"
    for order in orders[:10]:  # Show last 10
        message += (
            f"• `{order['order_number']}` - {format_price(order['total_amount'])}\n"
            f"  {order.get('first_name', 'N/A')} | {format_order_status(order['status'])}\n\n"
        )
    
    # Build keyboard with order buttons
    keyboard = []
    for order in orders[:10]:
        keyboard.append([
            InlineKeyboardButton(
                f"📦 {order['order_number']} - {format_order_status(order['status'])}",
                callback_data=f"admin_order_detail_{order['order_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_orders")])
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def admin_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin view order detail"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id not in ADMIN_IDS:
        await query.answer("❌ Unauthorized", show_alert=True)
        return
    
    order_id = int(query.data.split('_')[3])
    order = db.get_order(order_id)
    items = db.get_order_items(order_id)
    
    if not order:
        await query.edit_message_text(
            "❌ Order not found",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    user = db.get_user(order['user_id'])
    
    order_text = (
        f"📦 *Order Details*\n\n"
        f"Order ID: `{order['order_number']}`\n"
        f"Customer: {user['first_name']} (@{user['username']})\n"
        f"User ID: `{order['user_id']}`\n"
        f"Status: {format_order_status(order['status'])}\n"
        f"Date: {order['created_at']}\n"
        f"Total: {format_price(order['total_amount'])}\n\n"
        f"*Items:*\n"
    )
    
    for item in items:
        order_text += f"• {item['product_name']} x{item['quantity']} = {format_price(item['price'] * item['quantity'])}\n"
    
    if order['payment_proof']:
        order_text += f"\n📎 Payment proof available"
    
    # Send payment proof if exists
    if order['payment_proof'] and os.path.exists(order['payment_proof']):
        try:
            with open(order['payment_proof'], 'rb') as f:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=f,
                    caption=f"Payment proof for {order['order_number']}"
                )
        except Exception as e:
            logger.error(f"Failed to send payment proof: {e}")
    
    from keyboards.admin import get_admin_order_detail_keyboard
    await query.edit_message_text(
        order_text,
        reply_markup=get_admin_order_detail_keyboard(order_id, order['status']),
        parse_mode='Markdown'
    )
