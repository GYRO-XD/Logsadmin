import logging
import os
import uuid
from datetime import datetime
from config import ORDER_PREFIX, UPLOAD_DIR, PAYMENT_PROOFS_DIR

logger = logging.getLogger(__name__)

def generate_order_number():
    """Generate unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"{ORDER_PREFIX}{timestamp}{unique_id}"

def format_price(price):
    """Format price with currency symbol"""
    from config import CURRENCY_SYMBOL
    return f"{CURRENCY_SYMBOL}{price:,.2f}"

def format_order_status(status):
    """Format order status with emoji"""
    status_emojis = {
        'pending': '⏳ Pending',
        'approved': '✅ Approved',
        'completed': '✅ Completed',
        'rejected': '❌ Rejected',
        'cancelled': '🚫 Cancelled'
    }
    return status_emojis.get(status, status)

def truncate_text(text, max_length=50):
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def get_file_type(filename):
    """Get file type from extension"""
    ext = os.path.splitext(filename)[1].lower()
    type_map = {
        '.pdf': 'document',
        '.txt': 'document',
        '.doc': 'document',
        '.docx': 'document',
        '.jpg': 'photo',
        '.jpeg': 'photo',
        '.png': 'photo',
        '.gif': 'photo',
        '.mp4': 'video',
        '.avi': 'video',
        '.zip': 'archive',
        '.rar': 'archive',
        '.csv': 'spreadsheet',
        '.xlsx': 'spreadsheet'
    }
    return type_map.get(ext, 'file')

def paginate_list(items, page, items_per_page):
    """Paginate a list of items"""
    from config import ITEMS_PER_PAGE
    
    if items_per_page is None:
        items_per_page = ITEMS_PER_PAGE
    
    total_items = len(items)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    return items[start_idx:end_idx], total_pages, page

def validate_file_size(file_size, max_size_mb=50):
    """Validate file size"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

async def save_uploaded_file(file, directory, filename=None):
    """Save uploaded file to disk"""
    if filename is None:
        filename = f"{uuid.uuid4()}_{file.file_name}"
    
    file_path = os.path.join(directory, filename)
    
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Save file
    with open(file_path, 'wb') as f:
        if hasattr(file, 'get_file'):
            # For python-telegram-bot file objects
            file_data = await file.get_file()
            await file_data.download_to_drive(file_path)
        else:
            f.write(file)
    
    return file_path

def format_datetime(dt_string):
    """Format datetime string to readable format"""
    try:
        dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return dt_string

def escape_markdown(text):
    """Escape markdown special characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
