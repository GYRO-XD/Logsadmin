import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///marketplace.db')

# Payment Settings
BANK_NAME = os.getenv('BANK_NAME', 'Example Bank')
ACCOUNT_NAME = os.getenv('ACCOUNT_NAME', 'Marketplace Account')
ACCOUNT_NUMBER = os.getenv('ACCOUNT_NUMBER', '1234567890')

# Support
SUPPORT_TELEGRAM = os.getenv('SUPPORT_TELEGRAM', '@mrgyroxd')
SUPPORT_WHATSAPP = os.getenv('SUPPORT_WHATSAPP', 'https://wa.me/2347047543919')

# Bot Settings
ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', '5'))
CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '₦')
ORDER_PREFIX = os.getenv('ORDER_PREFIX', 'ORD')

# File Storage
UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'uploads')
PAYMENT_PROOFS_DIR = os.getenv('PAYMENT_PROOFS_DIR', 'payment_proofs')

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PAYMENT_PROOFS_DIR, exist_ok=True)
