import sqlite3
import os

DB_PATH = "restaurant.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the menu table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tag TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    
    # Check if we need to insert seed data
    cursor.execute("SELECT COUNT(*) FROM menu")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_data = [
            ("麻婆豆腐", "spicy", "经典川菜，麻辣鲜香", 18),
            ("糖醋里脊", "sweet", "酸甜可口，外酥里嫩", 32),
            ("麻辣小龙虾", "spicy", "夜宵必备，香辣过瘾", 58),
            ("桂花甜粥", "sweet", "清甜解腻，暖胃舒心", 12),
            ("扇贝", "sweet", "清甜解腻，暖胃舒心", 12),
            ("西湖醋鱼", "", "酸口", 12),
            ("南瓜粥", "", "，香甜，暖胃舒心", 12)
        ]
        cursor.executemany('''
            INSERT INTO menu (name, tag, description, price)
            VALUES (?, ?, ?, ?)
        ''', seed_data)
        print("Initialized database with seed data.")
        conn.commit()
    conn.close()

def get_all_menu():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu")
    results = cursor.fetchall()
    conn.close()
    
    items = []
    for row in results:
        items.append({
            "id": row[0],
            "name": row[1],
            "tag": row[2],
            "description": row[3],
            "price": row[4]
        })
    return items

def search_menu_by_tag(tag: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu WHERE tag = ?", (tag,))
    results = cursor.fetchall()
    conn.close()
    
    items = []
    for row in results:
        items.append({
            "id": row[0],
            "name": row[1],
            "tag": row[2],
            "description": row[3],
            "price": row[4]
        })
    return items
