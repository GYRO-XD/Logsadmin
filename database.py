
import sqlite3
import logging
from datetime import datetime
from config import DATABASE_URL

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = DATABASE_URL.replace('sqlite:///', '')
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER DEFAULT -1,
                is_active INTEGER DEFAULT 1,
                is_featured INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS product_files (
                file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_proof TEXT,
                admin_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            CREATE TABLE IF NOT EXISTS cart (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            CREATE TABLE IF NOT EXISTS wishlist (
                wishlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            CREATE TABLE IF NOT EXISTS admin_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS broadcast_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                recipients_count INTEGER DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Insert default settings
        cursor.executescript('''
            INSERT OR IGNORE INTO admin_settings (setting_key, setting_value) 
            VALUES ('payment_instructions', 'Bank Transfer\nBank: Example Bank\nAccount: 1234567890\nName: Marketplace Account');
            
            INSERT OR IGNORE INTO admin_settings (setting_key, setting_value) 
            VALUES ('support_info', 'Telegram: @mrgyroxd\nWhatsApp: https://wa.me/2347047543919');
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    # User Methods
    def add_user(self, user_id, username, first_name, last_name):
        conn = self.get_connection()
        conn.execute(
            'INSERT OR REPLACE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
            (user_id, username, first_name, last_name)
        )
        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = self.get_connection()
        user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        return user

    def get_all_users(self):
        conn = self.get_connection()
        users = conn.execute('SELECT * FROM users ORDER BY joined_date DESC').fetchall()
        conn.close()
        return users

    def search_users(self, query):
        conn = self.get_connection()
        users = conn.execute(
            'SELECT * FROM users WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?',
            (f'%{query}%', f'%{query}%', f'%{query}%')
        ).fetchall()
        conn.close()
        return users

    # Category Methods
    def add_category(self, name, description=''):
        conn = self.get_connection()
        cursor = conn.execute(
            'INSERT INTO categories (name, description) VALUES (?, ?)',
            (name, description)
        )
        conn.commit()
        category_id = cursor.lastrowid
        conn.close()
        return category_id

    def get_categories(self):
        conn = self.get_connection()
        categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
        conn.close()
        return categories

    def get_category(self, category_id):
        conn = self.get_connection()
        category = conn.execute('SELECT * FROM categories WHERE category_id = ?', (category_id,)).fetchone()
        conn.close()
        return category

    def update_category(self, category_id, name, description):
        conn = self.get_connection()
        conn.execute(
            'UPDATE categories SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE category_id = ?',
            (name, description, category_id)
        )
        conn.commit()
        conn.close()

    def delete_category(self, category_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM categories WHERE category_id = ?', (category_id,))
        conn.commit()
        conn.close()

    # Product Methods
    def add_product(self, name, description, price, category_id=None, stock=-1, is_featured=0):
        conn = self.get_connection()
        cursor = conn.execute(
            'INSERT INTO products (name, description, price, category_id, stock, is_featured) VALUES (?, ?, ?, ?, ?, ?)',
            (name, description, price, category_id, stock, is_featured)
        )
        conn.commit()
        product_id = cursor.lastrowid
        conn.close()
        return product_id

    def get_products(self, category_id=None, active_only=True):
        conn = self.get_connection()
        query = 'SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.category_id'
        conditions = []
        params = []
        
        if category_id is not None:
            conditions.append('p.category_id = ?')
            params.append(category_id)
        
        if active_only:
            conditions.append('p.is_active = 1')
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY p.created_at DESC'
        products = conn.execute(query, params).fetchall()
        conn.close()
        return products

    def get_product(self, product_id):
        conn = self.get_connection()
        product = conn.execute(
            'SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.category_id WHERE p.product_id = ?',
            (product_id,)
        ).fetchone()
        conn.close()
        return product

    def search_products(self, query):
        conn = self.get_connection()
        products = conn.execute(
            'SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.category_id WHERE p.name LIKE ? OR p.description LIKE ? AND p.is_active = 1',
            (f'%{query}%', f'%{query}%')
        ).fetchall()
        conn.close()
        return products

    def update_product(self, product_id, **kwargs):
        conn = self.get_connection()
        allowed_fields = ['name', 'description', 'price', 'category_id', 'stock', 'is_active', 'is_featured']
        updates = []
        params = []
        
        for field in allowed_fields:
            if field in kwargs:
                updates.append(f'{field} = ?')
                params.append(kwargs[field])
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(product_id)
            conn.execute(
                f'UPDATE products SET {", ".join(updates)} WHERE product_id = ?',
                params
            )
            conn.commit()
        conn.close()

    def delete_product(self, product_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        conn.commit()
        conn.close()

    def get_featured_products(self):
        conn = self.get_connection()
        products = conn.execute(
            'SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.category_id WHERE p.is_featured = 1 AND p.is_active = 1'
        ).fetchall()
        conn.close()
        return products

    def get_new_products(self, limit=10):
        conn = self.get_connection()
        products = conn.execute(
            'SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.category_id WHERE p.is_active = 1 ORDER BY p.created_at DESC LIMIT ?',
            (limit,)
        ).fetchall()
        conn.close()
        return products

    # File Methods
    def add_product_file(self, product_id, file_name, file_path, file_type):
        conn = self.get_connection()
        conn.execute(
            'INSERT INTO product_files (product_id, file_name, file_path, file_type) VALUES (?, ?, ?, ?)',
            (product_id, file_name, file_path, file_type)
        )
        conn.commit()
        conn.close()

    def get_product_files(self, product_id):
        conn = self.get_connection()
        files = conn.execute('SELECT * FROM product_files WHERE product_id = ?', (product_id,)).fetchall()
        conn.close()
        return files

    def delete_product_file(self, file_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM product_files WHERE file_id = ?', (file_id,))
        conn.commit()
        conn.close()

    # Order Methods
    def create_order(self, order_number, user_id, total_amount):
        conn = self.get_connection()
        cursor = conn.execute(
            'INSERT INTO orders (order_number, user_id, total_amount) VALUES (?, ?, ?)',
            (order_number, user_id, total_amount)
        )
        conn.commit()
        order_id = cursor.lastrowid
        conn.close()
        return order_id

    def add_order_item(self, order_id, product_id, quantity, price):
        conn = self.get_connection()
        conn.execute(
            'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
            (order_id, product_id, quantity, price)
        )
        conn.commit()
        conn.close()

    def get_order(self, order_id):
        conn = self.get_connection()
        order = conn.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)).fetchone()
        conn.close()
        return order

    def get_order_by_number(self, order_number):
        conn = self.get_connection()
        order = conn.execute('SELECT * FROM orders WHERE order_number = ?', (order_number,)).fetchone()
        conn.close()
        return order

    def get_user_orders(self, user_id):
        conn = self.get_connection()
        orders = conn.execute(
            'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        conn.close()
        return orders

    def get_all_orders(self, status=None):
        conn = self.get_connection()
        if status:
            orders = conn.execute(
                'SELECT o.*, u.username, u.first_name FROM orders o JOIN users u ON o.user_id = u.user_id WHERE o.status = ? ORDER BY o.created_at DESC',
                (status,)
            ).fetchall()
        else:
            orders = conn.execute(
                'SELECT o.*, u.username, u.first_name FROM orders o JOIN users u ON o.user_id = u.user_id ORDER BY o.created_at DESC'
            ).fetchall()
        conn.close()
        return orders

    def get_order_items(self, order_id):
        conn = self.get_connection()
        items = conn.execute(
            'SELECT oi.*, p.name as product_name FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE oi.order_id = ?',
            (order_id,)
        ).fetchall()
        conn.close()
        return items

    def update_order_status(self, order_id, status, admin_notes=''):
        conn = self.get_connection()
        conn.execute(
            'UPDATE orders SET status = ?, admin_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?',
            (status, admin_notes, order_id)
        )
        conn.commit()
        conn.close()

    def update_order_payment_proof(self, order_id, proof_path):
        conn = self.get_connection()
        conn.execute(
            'UPDATE orders SET payment_proof = ? WHERE order_id = ?',
            (proof_path, order_id)
        )
        conn.commit()
        conn.close()

    # Cart Methods
    def add_to_cart(self, user_id, product_id, quantity=1):
        conn = self.get_connection()
        existing = conn.execute(
            'SELECT * FROM cart WHERE user_id = ? AND product_id = ?',
            (user_id, product_id)
        ).fetchone()
        
        if existing:
            conn.execute(
                'UPDATE cart SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?',
                (quantity, user_id, product_id)
            )
        else:
            conn.execute(
                'INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)',
                (user_id, product_id, quantity)
            )
        conn.commit()
        conn.close()

    def get_cart(self, user_id):
        conn = self.get_connection()
        items = conn.execute(
            'SELECT c.*, p.name, p.price, p.stock FROM cart c JOIN products p ON c.product_id = p.product_id WHERE c.user_id = ?',
            (user_id,)
        ).fetchall()
        conn.close()
        return items

    def remove_from_cart(self, user_id, product_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        conn.commit()
        conn.close()

    def clear_cart(self, user_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    # Wishlist Methods
    def add_to_wishlist(self, user_id, product_id):
        conn = self.get_connection()
        try:
            conn.execute(
                'INSERT INTO wishlist (user_id, product_id) VALUES (?, ?)',
                (user_id, product_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()

    def remove_from_wishlist(self, user_id, product_id):
        conn = self.get_connection()
        conn.execute('DELETE FROM wishlist WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        conn.commit()
        conn.close()

    def get_wishlist(self, user_id):
        conn = self.get_connection()
        items = conn.execute(
            'SELECT w.*, p.name, p.price FROM wishlist w JOIN products p ON w.product_id = p.product_id WHERE w.user_id = ?',
            (user_id,)
        ).fetchall()
        conn.close()
        return items

    # Review Methods
    def add_review(self, user_id, product_id, rating, comment=''):
        conn = self.get_connection()
        conn.execute(
            'INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (?, ?, ?, ?)',
            (user_id, product_id, rating, comment)
        )
        conn.commit()
        conn.close()

    def get_product_reviews(self, product_id):
        conn = self.get_connection()
        reviews = conn.execute(
            'SELECT r.*, u.username, u.first_name FROM reviews r JOIN users u ON r.user_id = u.user_id WHERE r.product_id = ? ORDER BY r.created_at DESC',
            (product_id,)
        ).fetchall()
        conn.close()
        return reviews

    # Admin Settings Methods
    def get_setting(self, key):
        conn = self.get_connection()
        setting = conn.execute('SELECT setting_value FROM admin_settings WHERE setting_key = ?', (key,)).fetchone()
        conn.close()
        return setting['setting_value'] if setting else None

    def update_setting(self, key, value):
        conn = self.get_connection()
        conn.execute(
            'INSERT OR REPLACE INTO admin_settings (setting_key, setting_value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
            (key, value)
        )
        conn.commit()
        conn.close()

    # Broadcast Methods
    def log_broadcast(self, admin_id, message, recipients_count):
        conn = self.get_connection()
        conn.execute(
            'INSERT INTO broadcast_logs (admin_id, message, recipients_count) VALUES (?, ?, ?)',
            (admin_id, message, recipients_count)
        )
        conn.commit()
        conn.close()

    # Statistics Methods
    def get_sales_stats(self):
        conn = self.get_connection()
        stats = conn.execute('''
            SELECT 
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN total_amount ELSE 0 END), 0) as total_revenue,
                COUNT(DISTINCT user_id) as total_customers
            FROM orders
        ''').fetchone()
        conn.close()
        return stats

    def get_top_products(self, limit=5):
        conn = self.get_connection()
        products = conn.execute('''
            SELECT p.product_id, p.name, COUNT(oi.item_id) as order_count, SUM(oi.quantity * oi.price) as revenue
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status = 'completed'
            GROUP BY p.product_id
            ORDER BY order_count DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        conn.close()
        return products

# Create global database instance
db = Database()
