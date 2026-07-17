
#!/usr/bin/env python3
"""
Logs Admin - Telegram Marketplace Bot
A production-ready digital marketplace bot for Telegram
"""

import logging
import sys
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from config import BOT_TOKEN, ADMIN_IDS

# Import handlers
from handlers.customer import (
    start, main_menu, browse_products, show_category_products,
    show_uncategorized_products, show_product_detail, add_to_cart,
    view_cart, remove_from_cart, clear_cart, checkout,
    upload_payment_proof, handle_payment_proof, cancel_upload,
    view_order_detail, my_orders, add_to_wishlist,
    remove_from_wishlist, view_wishlist, search_products,
    handle_search, support, my_profile, buy_now, handle_quantity
)
from handlers.admin import (
    admin_panel, admin_products_menu, admin_list_products,
    admin_add_product_start, admin_add_product_name,
    admin_add_product_category, admin_add_product_description,
    admin_add_product_price, admin_add_product_stock,
    admin_receive_product_file, admin_edit_product,
    admin_delete_product, admin_confirm_delete_product,
    admin_toggle_product_status, admin_toggle_product_featured,
    admin_edit_product_field_start, admin_receive_edited_field,
    admin_categories_menu, admin_list_categories,
    admin_add_category_start, admin_add_category_name,
    admin_add_category_description, admin_users_menu,
    admin_list_users, admin_broadcast_start, admin_broadcast_send,
    admin_statistics, admin_sales_stats, admin_top_products,
    admin_settings, admin_edit_payment_instructions,
    admin_edit_support_info, admin_receive_setting,
    admin_cancel, manage_product_files, upload_product_file,
    handle_product_file_upload, delete_product_file,
    handle_search_user, handle_user_search_result
)
from handlers.payments import (
    approve_order, reject_order, cancel_order,
    admin_view_orders, admin_order_detail
)

# Conversation states
(SELECTING_QUANTITY, UPLOADING_PROOF, ADDING_PRODUCT, 
 EDITING_PRODUCT, ADDING_CATEGORY, BROADCASTING) = range(6)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LogsAdminBot:
    """Main bot application class"""
    
    def __init__(self):
        self.app = None
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later.\n"
                    "If the problem persists, contact support."
                )
        except:
            pass
    
    async def post_init(self, application: Application):
        """Post initialization hook"""
        logger.info("Bot started successfully!")
        logger.info(f"Admins configured: {len(ADMIN_IDS)}")
        
        # Notify admins that bot is online
        for admin_id in ADMIN_IDS:
            try:
                await application.bot.send_message(
                    chat_id=admin_id,
                    text="✅ *Logs Admin Marketplace Bot is Online!*\n\n"
                         "Use /admin to access the admin panel.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    def setup_handlers(self):
        """Setup all command and message handlers"""
        
        # Build the application
        self.app = Application.builder().token(BOT_TOKEN).post_init(self.post_init).build()
        
        # Add error handler
        self.app.add_error_handler(self.error_handler)
        
        # Customer conversation handler for payment proof upload
        payment_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(upload_payment_proof, pattern='^upload_proof_'),
                CallbackQueryHandler(buy_now, pattern='^buy_now_')
            ],
            states={
                UPLOADING_PROOF: [
                    MessageHandler(filters.PHOTO | filters.Document.ALL, handle_payment_proof),
                    CallbackQueryHandler(cancel_upload, pattern='^view_order_')
                ],
                SELECTING_QUANTITY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', cancel_upload),
                CallbackQueryHandler(main_menu, pattern='^main_menu$')
            ]
        )
        self.app.add_handler(payment_conv)
        
        # Admin conversation handler for adding products
        add_product_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(admin_add_product_start, pattern='^admin_add_product$')],
            states={
                ADDING_PRODUCT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_name),
                    CallbackQueryHandler(admin_add_product_category, pattern='^set_cat_'),
                    CallbackQueryHandler(admin_add_product_description, pattern='^skip_desc$'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_description),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_price),
                    CallbackQueryHandler(admin_add_product_stock, pattern='^set_stock_unlimited$'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_stock),
                    MessageHandler(filters.Document.ALL | filters.TEXT, admin_receive_product_file)
                ]
            },
            fallbacks=[CallbackQueryHandler(admin_cancel, pattern='^admin_products$')]
        )
        self.app.add_handler(add_product_conv)
        
        # Admin conversation handler for editing products
        edit_product_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(admin_edit_product_field_start, pattern='^edit_name_|^edit_desc_|^edit_price_|^edit_stock_'),
                CallbackQueryHandler(admin_edit_payment_instructions, pattern='^edit_payment_instructions$'),
                CallbackQueryHandler(admin_edit_support_info, pattern='^edit_support_info$')
            ],
            states={
                EDITING_PRODUCT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_edited_field),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_receive_setting)
                ]
            },
            fallbacks=[CallbackQueryHandler(admin_cancel, pattern='^admin_')]
        )
        self.app.add_handler(edit_product_conv)
        
        # Admin conversation handler for adding categories
        add_category_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(admin_add_category_start, pattern='^admin_add_category$')],
            states={
                ADDING_CATEGORY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_category_name),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_category_description)
                ]
            },
            fallbacks=[CallbackQueryHandler(admin_cancel, pattern='^admin_categories$')]
        )
        self.app.add_handler(add_category_conv)
        
        # Admin conversation handler for broadcasting
        broadcast_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(admin_broadcast_start, pattern='^admin_broadcast$')],
            states={
                BROADCASTING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)
                ]
            },
            fallbacks=[CallbackQueryHandler(admin_cancel, pattern='^admin_main$')]
        )
        self.app.add_handler(broadcast_conv)
        
        # Admin file upload conversation
        file_upload_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(upload_product_file, pattern='^upload_file_')],
            states={
                ADDING_PRODUCT: [
                    MessageHandler(filters.Document.ALL | filters.TEXT, handle_product_file_upload)
                ]
            },
            fallbacks=[CallbackQueryHandler(admin_cancel, pattern='^admin_')]
        )
        self.app.add_handler(file_upload_conv)
        
        # Command handlers
        self.app.add_handler(CommandHandler('start', start))
        self.app.add_handler(CommandHandler('admin', admin_panel))
        
        # Customer callback handlers
        self.app.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))
        self.app.add_handler(CallbackQueryHandler(browse_products, pattern='^browse_products$'))
        self.app.add_handler(CallbackQueryHandler(show_category_products, pattern='^category_'))
        self.app.add_handler(CallbackQueryHandler(show_uncategorized_products, pattern='^uncategorized_products$'))
        self.app.add_handler(CallbackQueryHandler(show_product_detail, pattern='^product_'))
        self.app.add_handler(CallbackQueryHandler(add_to_cart, pattern='^add_cart_'))
        self.app.add_handler(CallbackQueryHandler(view_cart, pattern='^view_cart$'))
        self.app.add_handler(CallbackQueryHandler(remove_from_cart, pattern='^remove_cart_'))
        self.app.add_handler(CallbackQueryHandler(clear_cart, pattern='^clear_cart$'))
        self.app.add_handler(CallbackQueryHandler(checkout, pattern='^checkout$'))
        self.app.add_handler(CallbackQueryHandler(view_order_detail, pattern='^order_detail_'))
        self.app.add_handler(CallbackQueryHandler(my_orders, pattern='^my_orders$'))
        self.app.add_handler(CallbackQueryHandler(add_to_wishlist, pattern='^add_wishlist_'))
        self.app.add_handler(CallbackQueryHandler(remove_from_wishlist, pattern='^remove_wishlist_'))
        self.app.add_handler(CallbackQueryHandler(view_wishlist, pattern='^view_wishlist$'))
        self.app.add_handler(CallbackQueryHandler(search_products, pattern='^search_products$'))
        self.app.add_handler(CallbackQueryHandler(support, pattern='^support$'))
        self.app.add_handler(CallbackQueryHandler(my_profile, pattern='^my_profile$'))
        
        # Product listing pagination
        self.app.add_handler(CallbackQueryHandler(
            lambda u, c: show_category_products(u, c), 
            pattern='^cat_page_'
        ))
        self.app.add_handler(CallbackQueryHandler(
            lambda u, c: browse_products(u, c), 
            pattern='^prod_page_'
        ))
        
        # Admin callback handlers
        self.app.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_main$'))
        self.app.add_handler(CallbackQueryHandler(admin_products_menu, pattern='^admin_products$'))
        self.app.add_handler(CallbackQueryHandler(admin_list_products, pattern='^admin_list_products$'))
        self.app.add_handler(CallbackQueryHandler(admin_edit_product, pattern='^admin_edit_product_'))
        self.app.add_handler(CallbackQueryHandler(admin_delete_product, pattern='^delete_product_'))
        self.app.add_handler(CallbackQueryHandler(admin_confirm_delete_product, pattern='^confirm_delete_product_'))
        self.app.add_handler(CallbackQueryHandler(admin_toggle_product_status, pattern='^toggle_active_'))
        self.app.add_handler(CallbackQueryHandler(admin_toggle_product_featured, pattern='^toggle_featured_'))
        self.app.add_handler(CallbackQueryHandler(admin_categories_menu, pattern='^admin_categories$'))
        self.app.add_handler(CallbackQueryHandler(admin_list_categories, pattern='^admin_list_categories$'))
        self.app.add_handler(CallbackQueryHandler(admin_users_menu, pattern='^admin_users$'))
        self.app.add_handler(CallbackQueryHandler(admin_list_users, pattern='^admin_all_users$'))
        self.app.add_handler(CallbackQueryHandler(admin_statistics, pattern='^admin_stats$'))
        self.app.add_handler(CallbackQueryHandler(admin_sales_stats, pattern='^stats_sales$'))
        self.app.add_handler(CallbackQueryHandler(admin_top_products, pattern='^stats_top_products$'))
        self.app.add_handler(CallbackQueryHandler(admin_settings, pattern='^admin_settings$'))
        self.app.add_handler(CallbackQueryHandler(manage_product_files, pattern='^manage_files_'))
        self.app.add_handler(CallbackQueryHandler(delete_product_file, pattern='^delete_file_'))
        self.app.add_handler(CallbackQueryHandler(handle_search_user, pattern='^admin_search_user$'))
        
        # Order management
        self.app.add_handler(CallbackQueryHandler(admin_view_orders, pattern='^admin_all_orders$|^admin_pending_orders$|^admin_completed_orders$|^admin_rejected_orders$'))
        self.app.add_handler(CallbackQueryHandler(admin_order_detail, pattern='^admin_order_detail_'))
        self.app.add_handler(CallbackQueryHandler(approve_order, pattern='^approve_order_'))
        self.app.add_handler(CallbackQueryHandler(reject_order, pattern='^reject_order_'))
        self.app.add_handler(CallbackQueryHandler(cancel_order, pattern='^cancel_order_'))
        
        # Message handlers for search
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.UpdateType.MESSAGE,
            self.handle_messages
        ))
        
        # Default handler for admin menu navigation
        self.app.add_handler(CallbackQueryHandler(
            lambda u, c: admin_panel(u, c) if u.callback_query.data.startswith('admin_') else None,
            pattern='^admin_orders$|^admin_payments$'
        ))
    
    async def handle_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages based on context"""
        user_data = context.user_data
        
        if user_data.get('expecting_search'):
            await handle_search(update, context)
        elif user_data.get('searching_user'):
            await handle_user_search_result(update, context)
        elif user_data.get('expecting_files'):
            await admin_receive_product_file(update, context)
        elif user_data.get('expecting_product_file'):
            await handle_product_file_upload(update, context)
        else:
            # Default response
            await update.message.reply_text(
                "I didn't understand that. Use /start to see the main menu.",
                reply_markup=None
            )
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Logs Admin Marketplace Bot...")
        self.setup_handlers()
        
        # Start polling
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main entry point"""
    if not BOT_TOKEN or BOT_TOKEN == 'your_bot_token_here':
        logger.error("Bot token not configured! Please set BOT_TOKEN in .env file")
        sys.exit(1)
    
    bot = LogsAdminBot()
    bot.run()

if __name__ == '__main__':
    main()
