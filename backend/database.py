import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ecommerce_sample.db")

def get_db_connection(db_file=None):
    target_path = db_file or DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_and_seed_db(db_file=None):
    target_path = db_file or DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()

    # Drop existing tables for clean setup
    cursor.executescript("""
        DROP TABLE IF EXISTS fulfillment_workflows;
        DROP TABLE IF EXISTS inventory_logs;
        DROP TABLE IF EXISTS reviews;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS categories;
        DROP TABLE IF EXISTS customers;
    """)

    # Schema creation
    cursor.executescript("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            country TEXT NOT NULL,
            user_segment TEXT NOT NULL,
            signup_date DATE NOT NULL
        );

        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL,
            description TEXT
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL,
            rating REAL NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (category_id)
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date DATE NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            shipping_country TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        );

        CREATE TABLE order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (order_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        );

        CREATE TABLE reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            review_date DATE NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (product_id),
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        );

        CREATE TABLE inventory_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            change_qty INTEGER NOT NULL,
            reason TEXT NOT NULL,
            log_timestamp DATETIME NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        );

        CREATE TABLE fulfillment_workflows (
            workflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            current_stage TEXT NOT NULL,
            updated_at DATETIME NOT NULL,
            estimated_delivery DATE NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (order_id)
        );
    """)

    # Seed Categories
    categories = [
        ("Electronics", "Gadgets, computing, audio, and personal devices"),
        ("Apparel & Fashion", "Clothing, shoes, and luxury accessories"),
        ("Home & Kitchen", "Furniture, cookware, and smart home items"),
        ("Books & Media", "Printed books, e-readers, and educational content"),
        ("Fitness & Sports", "Workout gear, outdoor equipment, and sports wear")
    ]
    cursor.executemany("INSERT INTO categories (category_name, description) VALUES (?, ?)", categories)

    # Seed Products
    products = [
        (1, "AuraSound Noise-Canceling Headphones", 249.99, 120, 4.8),
        (1, "QuantumBook Pro 15 Laptop", 1299.00, 45, 4.9),
        (1, "VividPixel 4K Smart Monitor", 389.50, 60, 4.6),
        (1, "SmartSync Fitness Watch 3", 179.95, 210, 4.5),
        (1, "SonicPro Wireless Earbuds", 119.00, 300, 4.3),
        (2, "Merino Wool Executive Blazer", 299.00, 50, 4.7),
        (2, "UrbanTrek All-Weather Boots", 149.99, 90, 4.6),
        (2, "Silk Breeze Summer Dress", 89.50, 110, 4.4),
        (2, "Classic Leather Messenger Bag", 135.00, 80, 4.8),
        (3, "BaristaPro Espresso Machine", 450.00, 35, 4.9),
        (3, "ErgoFlex Ergonomic Office Chair", 320.00, 75, 4.7),
        (3, "ChefKnife Titanium 8-inch Knife", 65.00, 180, 4.8),
        (3, "AeroPure HEPA Air Purifier", 159.99, 95, 4.5),
        (4, "Mastering Modern AI & Agents", 49.99, 400, 4.9),
        (4, "The Art of Data Engineering", 39.50, 320, 4.8),
        (4, "Deep Learning Architecture Guide", 59.00, 150, 4.7),
        (5, "FlexCore Power Dumbbell Set", 199.99, 85, 4.6),
        (5, "TrailBlazer Carbon Trekking Poles", 79.99, 140, 4.5),
        (5, "ZenFlow Non-Slip Yoga Mat", 42.00, 250, 4.7),
        (5, "HydroShield Insulated Water Bottle", 28.50, 500, 4.8)
    ]
    cursor.executemany("INSERT INTO products (category_id, product_name, price, stock_quantity, rating) VALUES (?, ?, ?, ?, ?)", products)

    # Seed Customers
    first_names = ["Alex", "Sophia", "Liam", "Emma", "Noah", "Olivia", "Ethan", "Ava", "Lucas", "Isabella", "Mason", "Mia", "James", "Harper", "Benjamin"]
    last_names = ["Smith", "Johnson", "Brown", "Taylor", "Miller", "Wilson", "Moore", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Clark"]
    countries = ["United States", "Canada", "United Kingdom", "Germany", "France", "Japan", "Australia", "Singapore"]
    segments = ["VIP", "Regular", "Enterprise", "New"]

    customers = []
    random.seed(42)
    start_date = datetime(2025, 1, 1)

    for i in range(1, 41):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        name = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
        country = random.choice(countries)
        segment = random.choice(segments)
        s_date = (start_date + timedelta(days=random.randint(0, 350))).strftime("%Y-%m-%d")
        customers.append((name, email, country, segment, s_date))
    
    cursor.executemany("INSERT INTO customers (name, email, country, user_segment, signup_date) VALUES (?, ?, ?, ?, ?)", customers)

    # Seed Orders & Order Items
    statuses = ["Completed", "Completed", "Completed", "Processing", "Shipped", "Cancelled"]
    pay_methods = ["Credit Card", "Credit Card", "PayPal", "Bank Transfer", "Crypto"]
    
    order_id = 1
    orders = []
    order_items = []
    inventory_logs = []
    fulfillment_workflows = []

    order_start = datetime(2025, 6, 1)
    stages = ["Order Placed", "Payment Verified", "Inventory Allocated", "Packaging", "Shipped", "Out for Delivery", "Delivered"]

    for i in range(1, 101):
        cust_id = random.randint(1, 40)
        o_date = (order_start + timedelta(days=random.randint(0, 240))).strftime("%Y-%m-%d")
        status = random.choice(statuses)
        pay_method = random.choice(pay_methods)
        cust_country = customers[cust_id - 1][2]
        
        # Pick 1 to 4 items for this order
        num_items = random.randint(1, 4)
        selected_prods = random.sample(products, num_items)
        
        total_amount = 0.0
        for prod in selected_prods:
            prod_id = products.index(prod) + 1
            qty = random.randint(1, 3)
            unit_price = prod[2]
            subtotal = round(qty * unit_price, 2)
            total_amount += subtotal
            order_items.append((order_id, prod_id, qty, unit_price, subtotal))
            
            # Add inventory log entry
            log_time = f"{o_date} {random.randint(8, 18):02d}:{random.randint(10, 59):02d}:00"
            inventory_logs.append((prod_id, -qty, "Order Sale", log_time))

        total_amount = round(total_amount, 2)
        orders.append((order_id, cust_id, o_date, total_amount, status, pay_method, cust_country))

        # Workflow stage
        stage = "Delivered" if status == "Completed" else ("Shipped" if status == "Shipped" else random.choice(stages[:4]))
        est_del = (datetime.strptime(o_date, "%Y-%m-%d") + timedelta(days=5)).strftime("%Y-%m-%d")
        fulfillment_workflows.append((order_id, stage, f"{o_date} 12:00:00", est_del))

        order_id += 1

    cursor.executemany("INSERT INTO orders (order_id, customer_id, order_date, total_amount, status, payment_method, shipping_country) VALUES (?, ?, ?, ?, ?, ?, ?)", orders)
    cursor.executemany("INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (?, ?, ?, ?, ?)", order_items)
    cursor.executemany("INSERT INTO inventory_logs (product_id, change_qty, reason, log_timestamp) VALUES (?, ?, ?, ?)", inventory_logs)
    cursor.executemany("INSERT INTO fulfillment_workflows (order_id, current_stage, updated_at, estimated_delivery) VALUES (?, ?, ?, ?)", fulfillment_workflows)

    # Seed Reviews
    sample_comments = [
        "Absolutely amazing quality! Exceeded my expectations.",
        "Good value for money. Very fast shipping.",
        "Slightly smaller than expected, but works well.",
        "Build quality is premium. High performance!",
        "Customer service was super helpful with my questions.",
        "Works as advertised, will buy again."
    ]
    reviews = []
    for _ in range(50):
        p_id = random.randint(1, len(products))
        c_id = random.randint(1, len(customers))
        rating = random.choices([5, 4, 3, 2, 1], weights=[50, 30, 10, 6, 4])[0]
        cmt = random.choice(sample_comments)
        r_date = (order_start + timedelta(days=random.randint(0, 240))).strftime("%Y-%m-%d")
        reviews.append((p_id, c_id, rating, cmt, r_date))

    cursor.executemany("INSERT INTO reviews (product_id, customer_id, rating, comment, review_date) VALUES (?, ?, ?, ?, ?)", reviews)

    conn.commit()
    conn.close()

    # Also ensure chat history tables exist
    init_chat_history_db(target_path)
    return target_path


def init_chat_history_db(db_file=None):
    conn = get_db_connection(db_file)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            metadata_json TEXT,
            timestamp TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def get_all_chat_sessions(db_file=None):
    init_chat_history_db(db_file)
    conn = get_db_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.session_id, s.title, s.created_at, s.updated_at, COUNT(m.message_id) as message_count
        FROM chat_sessions s
        LEFT JOIN chat_messages m ON s.session_id = m.session_id
        GROUP BY s.session_id
        ORDER BY s.updated_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_chat_session(session_id: str, db_file=None):
    init_chat_history_db(db_file)
    conn = get_db_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, title, created_at, updated_at FROM chat_sessions WHERE session_id = ?", (session_id,))
    session = cursor.fetchone()
    if not session:
        conn.close()
        return None

    cursor.execute("""
        SELECT message_id, role, content, metadata_json, timestamp
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY rowid ASC
    """, (session_id,))
    msg_rows = cursor.fetchall()
    conn.close()

    import json
    messages = []
    for r in msg_rows:
        meta = json.loads(r["metadata_json"]) if r["metadata_json"] else {}
        msg = {
            "id": r["message_id"],
            "role": r["role"],
            "content": r["content"],
            "timestamp": r["timestamp"],
            **meta
        }
        messages.append(msg)

    res = dict(session)
    res["messages"] = messages
    return res


def save_chat_session(session_id: str, title: str, messages: list, db_file=None):
    init_chat_history_db(db_file)
    conn = get_db_connection(db_file)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO chat_sessions (session_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET title=excluded.title, updated_at=excluded.updated_at
    """, (session_id, title or "Untitled Session", now_str, now_str))

    # Clear existing messages for session and insert current messages batch
    cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    
    import json
    msg_inserts = []
    for idx, m in enumerate(messages):
        msg_id = m.get("id") or f"{session_id}_msg_{idx}"
        role = m.get("role", "user")
        content = m.get("content", "")
        timestamp = m.get("timestamp", "")
        
        # Extract extra fields to store in metadata_json
        reserved_keys = {"id", "role", "content", "timestamp"}
        meta = {k: v for k, v in m.items() if k not in reserved_keys}
        meta_json = json.dumps(meta) if meta else None

        msg_inserts.append((msg_id, session_id, role, content, meta_json, timestamp))

    cursor.executemany("""
        INSERT INTO chat_messages (message_id, session_id, role, content, metadata_json, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, msg_inserts)

    conn.commit()
    conn.close()
    return {"status": "success", "session_id": session_id}


def delete_chat_session(session_id: str, db_file=None):
    init_chat_history_db(db_file)
    conn = get_db_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "session_id": session_id}


def clear_all_chat_sessions(db_file=None):
    init_chat_history_db(db_file)
    conn = get_db_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages")
    cursor.execute("DELETE FROM chat_sessions")
    conn.commit()
    conn.close()
    return {"status": "cleared"}


if __name__ == "__main__":
    path = init_and_seed_db()
    print(f"Database successfully initialized and seeded at: {path}")

