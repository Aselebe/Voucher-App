import sqlite3
import os

def get_db_connection():
    try:
        db_path = os.path.abspath('voucher.db')
        print(f"Connecting to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def create_tables():
    conn = get_db_connection()

    conn.execute('''
    CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY,
        event_name TEXT NOT NULL,
        event_date TEXT NOT NULL
    )
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS vendors (
        vendor_id TEXT PRIMARY KEY,
        vendor_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        password TEXT,
        event_id TEXT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(event_id)
    )
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS vouchers (
        voucher_id TEXT PRIMARY KEY,
        voucher_name TEXT NOT NULL,
        email TEXT NOT NULL,
        balance REAL NOT NULL,
        canceled INTEGER DEFAULT 0
    )
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        voucher_id TEXT,
        booth_id TEXT,
        sale_amount REAL,
        sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (voucher_id) REFERENCES vouchers(voucher_id),
        FOREIGN KEY (booth_id) REFERENCES vendors(vendor_id)
    )
    ''')
    conn.commit()
    conn.close()