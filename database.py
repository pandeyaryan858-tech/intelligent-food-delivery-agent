"""
database.py — Student 1: Database and Order Management
Project: Intelligent Food Delivery Agent

Run this file directly to create food_delivery.db and perform a small test:
    python database.py

Sample food prices are illustrative; change them if your group has agreed prices.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("food_delivery.db")

FOOD_ITEMS = [
    ("Burger", 80.0),
    ("Sandwich", 60.0),
    ("Pizza", 150.0),
    ("Juice", 40.0),
]

LOCATIONS = [
    "Vivekananda",
    "Vedanta",
    "Charak",
    "Vaastu",
    "Chanakya",
    "Vishwakarma",
    "Visvesvaraya",
]

DELIVERY_DESTINATIONS = {
    "Vedanta",
    "Charak",
    "Vaastu",
    "Chanakya",
    "Vishwakarma",
    "Visvesvaraya",
}

VALID_PRIORITIES = {"High", "Normal", "Low"}
VALID_STATUSES = {"Pending", "Planned", "Delivered", "Cancelled"}


def _connect():
    """Open a database connection and enable SQLite foreign-key checks."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """
    Create tables if missing and add sample data only when it is missing.
    Existing orders are not deleted when this function is called again.
    """
    with _connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS food_items (
                food_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL CHECK (price >= 0)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                food_item TEXT NOT NULL,
                destination TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                priority TEXT NOT NULL CHECK (priority IN ('High', 'Normal', 'Low')),
                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK (status IN ('Pending', 'Planned', 'Delivered', 'Cancelled')),
                FOREIGN KEY (food_item) REFERENCES food_items(name),
                FOREIGN KEY (destination) REFERENCES locations(name)
            )
        """)

        # INSERT OR IGNORE prevents duplicate sample rows on later app starts.
        connection.executemany(
            "INSERT OR IGNORE INTO food_items (name, price) VALUES (?, ?)",
            FOOD_ITEMS,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO locations (name) VALUES (?)",
            [(name,) for name in LOCATIONS],
        )


def get_food_items():
    """Return food items as a list of dictionaries: food_id, name, price."""
    with _connect() as connection:
        rows = connection.execute(
            "SELECT food_id, name, price FROM food_items ORDER BY food_id"
        ).fetchall()
        return [dict(row) for row in rows]


def get_locations():
    """Return campus locations as dictionaries: location_id, name."""
    with _connect() as connection:
        rows = connection.execute(
            "SELECT location_id, name FROM locations ORDER BY location_id"
        ).fetchall()
        return [dict(row) for row in rows]


def place_order(customer, food_item, destination, priority, quantity=1):
    """
    Save a new order and return its integer order_id.

    food_item must match a seeded food name. destination must be one of the
    six delivery buildings (Vivekananda is the cafeteria/start location).
    """
    if not isinstance(customer, str) or not customer.strip():
        raise ValueError("Customer name cannot be empty.")

    if not isinstance(food_item, str) or not food_item.strip():
        raise ValueError("Please select a food item.")

    if not isinstance(destination, str) or destination not in DELIVERY_DESTINATIONS:
        raise ValueError("Destination must be one of the six delivery buildings.")

    if priority not in VALID_PRIORITIES:
        raise ValueError("Priority must be High, Normal, or Low.")

    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise ValueError("Quantity must be a positive whole number.")

    with _connect() as connection:
        food_exists = connection.execute(
            "SELECT 1 FROM food_items WHERE name = ?", (food_item,)
        ).fetchone()
        if food_exists is None:
            raise ValueError(f"Unknown food item: {food_item}")

        location_exists = connection.execute(
            "SELECT 1 FROM locations WHERE name = ?", (destination,)
        ).fetchone()
        if location_exists is None:
            raise ValueError(f"Unknown destination: {destination}")

        cursor = connection.execute(
            """
            INSERT INTO orders
                (customer, food_item, destination, quantity, priority, status)
            VALUES (?, ?, ?, ?, ?, 'Pending')
            """,
            (customer.strip(), food_item, destination, quantity, priority),
        )
        return cursor.lastrowid


def get_pending_orders():
    """
    Return pending orders as a list of dictionaries.

    Exact keys in each dictionary:
    order_id, customer, food_item, destination, quantity, priority, status.
    These keys are intended for delivery_planner.py and app.py.
    """
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT order_id, customer, food_item, destination,
                   quantity, priority, status
            FROM orders
            WHERE status = 'Pending'
            ORDER BY order_id
            """
        ).fetchall()
        return [dict(row) for row in rows]


def update_order_status(order_id, status):
    """
    Update an order's status. Return True if an existing order was updated,
    otherwise False. Allowed statuses: Pending, Planned, Delivered, Cancelled.
    """
    if status not in VALID_STATUSES:
        raise ValueError(
            "Status must be Pending, Planned, Delivered, or Cancelled."
        )

    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (status, order_id),
        )
        return cursor.rowcount > 0


if __name__ == "__main__":
    initialize_database()
    print("Database initialized:", DB_PATH)
    print("\nFood items:")
    for item in get_food_items():
        print(item)

    print("\nCampus locations:")
    for location in get_locations():
        print(location)

    print("\nPending orders already in the database:")
    for order in get_pending_orders():
        print(order)

    # To test placing an order, run this in a separate test file or Python shell:
    # from database import initialize_database, place_order
    # initialize_database()
    # order_id = place_order("Demo Student", "Sandwich", "Vedanta", "Normal", 1)
    # print("Created order ID:", order_id)
