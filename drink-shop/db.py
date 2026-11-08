"""資料庫與工具函式：飲料店點餐系統。

這裡的每個函式都會交給 Gemini 當作「工具」(tool calling)。
模型會根據使用者的話，自己決定要呼叫哪一個函式。
函式的 docstring 和型別提示會被傳給模型，所以要寫清楚。
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "drinks.db"

SIZES = {"M": 0, "L": 10}  # 大杯加 10 元
SUGAR_LEVELS = ["正常糖", "少糖", "半糖", "微糖", "無糖"]
ICE_LEVELS = ["正常冰", "少冰", "微冰", "去冰", "溫", "熱"]

# 假資料（自己編的）：品名, 分類, 中杯價格
MENU = [
    ("珍珠奶茶", "奶茶", 55),
    ("波霸奶茶", "奶茶", 55),
    ("鮮奶茶", "奶茶", 60),
    ("黑糖珍珠鮮奶", "奶茶", 70),
    ("紅茶拿鐵", "奶茶", 60),
    ("四季春青茶", "純茶", 30),
    ("茉莉綠茶", "純茶", 30),
    ("阿薩姆紅茶", "純茶", 30),
    ("烏龍茶", "純茶", 35),
    ("檸檬綠茶", "果茶", 50),
    ("百香果綠茶", "果茶", 55),
    ("葡萄柚綠茶", "果茶", 60),
    ("冬瓜檸檬", "果茶", 45),
    ("多多綠茶", "特調", 50),
    ("芒果冰沙", "冰沙", 75),
]


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建立資料表，第一次執行時放入菜單。"""
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS drinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                price_m INTEGER NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                drink_name TEXT NOT NULL,
                size TEXT NOT NULL,
                sugar TEXT NOT NULL,
                ice TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT '已成立',
                created_at TEXT NOT NULL
            )"""
        )
        if conn.execute("SELECT COUNT(*) FROM drinks").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO drinks (name, category, price_m) VALUES (?, ?, ?)", MENU
            )


def _find_drink(conn, drink_name: str):
    return conn.execute(
        "SELECT * FROM drinks WHERE name = ?", (drink_name.strip(),)
    ).fetchone()


# ---------------- 以下是給模型使用的工具 ----------------


def get_menu() -> dict:
    """取得完整菜單，包含每個飲料的名稱、分類、中杯(M)和大杯(L)價格。

    當使用者問「有什麼飲料」、「菜單」、「推薦」時使用。
    """
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM drinks ORDER BY category, id").fetchall()
    return {
        "drinks": [
            {
                "name": r["name"],
                "category": r["category"],
                "price_M": r["price_m"],
                "price_L": r["price_m"] + SIZES["L"],
            }
            for r in rows
        ],
        "sugar_options": SUGAR_LEVELS,
        "ice_options": ICE_LEVELS,
    }


def get_drink_price(drink_name: str) -> dict:
    """查詢某一個飲料的價格。

    Args:
        drink_name: 飲料的完整名稱，必須和菜單上的名稱一樣，例如「珍珠奶茶」。
    """
    with _connect() as conn:
        drink = _find_drink(conn, drink_name)
    if drink is None:
        return {"found": False, "message": f"菜單上沒有「{drink_name}」。"}
    return {
        "found": True,
        "name": drink["name"],
        "price_M": drink["price_m"],
        "price_L": drink["price_m"] + SIZES["L"],
    }


def place_order(
    customer_name: str,
    drink_name: str,
    size: str,
    sugar: str,
    ice: str,
    quantity: int,
) -> dict:
    """建立一筆新訂單並存進資料庫。只有在使用者確認所有內容後才能呼叫。

    Args:
        customer_name: 顧客的名字或稱呼。
        drink_name: 飲料的完整名稱，必須和菜單上的名稱一樣。
        size: 杯型，只能是 "M"（中杯）或 "L"（大杯）。
        sugar: 甜度，只能是：正常糖、少糖、半糖、微糖、無糖。
        ice: 冰塊，只能是：正常冰、少冰、微冰、去冰、溫、熱。
        quantity: 杯數，1 到 20 之間的整數。
    """
    size = size.strip().upper()
    if size not in SIZES:
        return {"success": False, "message": "杯型只能是 M 或 L。"}
    if sugar not in SUGAR_LEVELS:
        return {"success": False, "message": f"甜度只能是：{'、'.join(SUGAR_LEVELS)}。"}
    if ice not in ICE_LEVELS:
        return {"success": False, "message": f"冰塊只能是：{'、'.join(ICE_LEVELS)}。"}
    quantity = int(quantity)
    if not 1 <= quantity <= 20:
        return {"success": False, "message": "杯數必須是 1 到 20 杯。"}
    if not customer_name.strip():
        return {"success": False, "message": "需要顧客的名字。"}

    with _connect() as conn:
        drink = _find_drink(conn, drink_name)
        if drink is None:
            return {"success": False, "message": f"菜單上沒有「{drink_name}」。"}

        total = (drink["price_m"] + SIZES[size]) * quantity
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        order_id = f"A{count + 1:03d}"
        conn.execute(
            """INSERT INTO orders (order_id, customer_name, drink_name, size, sugar,
                   ice, quantity, total_price, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                order_id,
                customer_name.strip(),
                drink["name"],
                size,
                sugar,
                ice,
                quantity,
                total,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
    return {"success": True, "order_id": order_id, "total_price": total}


def get_order(order_id: str) -> dict:
    """用訂單編號查詢訂單內容和狀態。

    Args:
        order_id: 訂單編號，格式像 "A001"。
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id.strip().upper(),)
        ).fetchone()
    if row is None:
        return {"found": False, "message": f"找不到訂單 {order_id}。"}
    return {"found": True, **dict(row)}


def cancel_order(order_id: str) -> dict:
    """取消一筆訂單。只有在使用者明確說要取消時才能呼叫。

    Args:
        order_id: 要取消的訂單編號，格式像 "A001"。
    """
    order_id = order_id.strip().upper()
    with _connect() as conn:
        row = conn.execute(
            "SELECT status FROM orders WHERE order_id = ?", (order_id,)
        ).fetchone()
        if row is None:
            return {"success": False, "message": f"找不到訂單 {order_id}。"}
        if row["status"] == "已取消":
            return {"success": False, "message": f"訂單 {order_id} 已經取消過了。"}
        conn.execute(
            "UPDATE orders SET status = '已取消' WHERE order_id = ?", (order_id,)
        )
    return {"success": True, "message": f"訂單 {order_id} 已取消。"}


def list_orders() -> list:
    """給「訂單列表」頁面使用（不是給模型的工具）。"""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    return [
        [r["order_id"], r["customer_name"], r["drink_name"], r["size"], r["sugar"],
         r["ice"], r["quantity"], r["total_price"], r["status"], r["created_at"]]
        for r in rows
    ]


TOOLS = [get_menu, get_drink_price, place_order, get_order, cancel_order]
