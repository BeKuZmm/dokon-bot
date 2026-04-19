import sqlite3
from datetime import datetime
from typing import List, Optional


class Database:
    def __init__(self, db_path: str = "dokon.db"):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    image_url TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_id INTEGER,
                    qty INTEGER DEFAULT 1,
                    UNIQUE(user_id, product_id)
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    phone TEXT,
                    address TEXT,
                    total INTEGER,
                    status TEXT DEFAULT 'yangi',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    product_id INTEGER,
                    product_name TEXT,
                    price INTEGER,
                    qty INTEGER
                );
            """)

    # ── USERS ──────────────────────────────────────────────

    def add_user(self, user_id: int, username: str, full_name: str):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, username, full_name) VALUES (?, ?, ?)",
                (user_id, username, full_name)
            )

    def is_admin(self, user_id: int) -> bool:
        with self._conn() as conn:
            row = conn.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,)).fetchone()
            return row is not None

    def get_admin_ids(self) -> List[int]:
        with self._conn() as conn:
            rows = conn.execute("SELECT user_id FROM admins").fetchall()
            return [r[0] for r in rows]

    def add_admin(self, user_id: int):
        with self._conn() as conn:
            conn.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))

    # ── PRODUCTS ───────────────────────────────────────────

    def add_product(self, name: str, description: str, price: int,
                    category: str, image_url: Optional[str] = None) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO products (name, description, price, category, image_url) VALUES (?, ?, ?, ?, ?)",
                (name, description, price, category, image_url)
            )
            return cur.lastrowid

    def get_categories(self) -> List[str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT category FROM products WHERE is_active = 1 ORDER BY category"
            ).fetchall()
            return [r[0] for r in rows]

    def get_products_by_category(self, category: str) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE category = ? AND is_active = 1",
                (category,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_product(self, product_id: int) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_products(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE is_active = 1 ORDER BY category, name"
            ).fetchall()
            return [dict(r) for r in rows]

    def deactivate_product(self, product_id: int):
        with self._conn() as conn:
            conn.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))

    # ── CART ───────────────────────────────────────────────

    def add_to_cart(self, user_id: int, product_id: int):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO cart (user_id, product_id, qty) VALUES (?, ?, 1)
                   ON CONFLICT(user_id, product_id) DO UPDATE SET qty = qty + 1""",
                (user_id, product_id)
            )

    def get_cart(self, user_id: int) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT c.product_id, c.qty, p.name, p.price
                   FROM cart c JOIN products p ON c.product_id = p.id
                   WHERE c.user_id = ?""",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def update_cart_qty(self, user_id: int, product_id: int, delta: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE cart SET qty = MAX(0, qty + ?) WHERE user_id = ? AND product_id = ?",
                (delta, user_id, product_id)
            )
            conn.execute(
                "DELETE FROM cart WHERE user_id = ? AND product_id = ? AND qty = 0",
                (user_id, product_id)
            )

    def remove_from_cart(self, user_id: int, product_id: int):
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM cart WHERE user_id = ? AND product_id = ?",
                (user_id, product_id)
            )

    def clear_cart(self, user_id: int):
        with self._conn() as conn:
            conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))

    # ── ORDERS ─────────────────────────────────────────────

    def create_order(self, user_id: int, phone: str, address: str,
                     items: List[dict], total: int) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO orders (user_id, phone, address, total) VALUES (?, ?, ?, ?)",
                (user_id, phone, address, total)
            )
            order_id = cur.lastrowid
            for item in items:
                conn.execute(
                    "INSERT INTO order_items (order_id, product_id, product_name, price, qty) VALUES (?, ?, ?, ?, ?)",
                    (order_id, item['product_id'], item['name'], item['price'], item['qty'])
                )
            return order_id

    def get_user_orders(self, user_id: int) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_orders(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT 50"
            ).fetchall()
            return [dict(r) for r in rows]

    def update_order_status(self, order_id: int, status: str):
        with self._conn() as conn:
            conn.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id)
            )

    def get_order_items(self, order_id: int) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
            ).fetchall()
            return [dict(r) for r in rows]
