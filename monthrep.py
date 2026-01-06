# Monthly report module - monthly revenue generated and the orders of the month displayed
# Flask-compatible module for generating monthly reports from database

import sqlite3
from datetime import datetime

# Database file name
DB_FILE = 'customer_db.sqlite'


def init_orders_database():
    """
    Initialize the SQLite database and create orders table if it doesn't exist.
    Also migrates data from CSV file if database is empty.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create orders table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            pickup_address TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            order_pickup_date TEXT NOT NULL,
            order_delivery_date TEXT NOT NULL,
            bill_amount REAL NOT NULL CHECK(bill_amount >= 0),
            bill_id TEXT UNIQUE NOT NULL,
            delivery_status TEXT NOT NULL DEFAULT 'Order Placed'
                CHECK(delivery_status IN ('Order Placed', 'Order Picked', 'In Process', 'Out for Delivery', 'Delivered', 'Cancelled')),
            cancelled_by TEXT CHECK(cancelled_by IN ('customer', NULL)),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def get_monthly_orders(month=None, year=None):
    """
    Get orders from database filtered by month and year.
    Orders are returned in descending order of delivery date.
    
    Args:
        month (int): Month number (1-12). If None, returns all orders.
        year (int): Year number. If None, uses current year.
    
    Returns:
        list: List of dictionaries containing order information
    """
    init_orders_database()
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        if month is None and year is None:
            # Get all orders, sorted by delivery date descending
            # Date format is DD-MM-YYYY, convert to YYYY-MM-DD for proper sorting
            cursor.execute('''
                SELECT customer_id, customer_name, order_pickup_date, order_delivery_date,
                       bill_amount, bill_id, delivery_status
                FROM orders
                ORDER BY
                    CASE
                        WHEN length(order_delivery_date) = 10 AND substr(order_delivery_date, 3, 1) = '-' THEN
                            substr(order_delivery_date, 7, 4) || '-' ||
                            substr(order_delivery_date, 4, 2) || '-' ||
                            substr(order_delivery_date, 1, 2)
                        ELSE order_delivery_date
                    END DESC
            ''')
        elif month is None and year is not None:
            # Filter by year only
            year_str = str(year)

            cursor.execute('''
                SELECT customer_id, customer_name, order_pickup_date, order_delivery_date,
                       bill_amount, bill_id, delivery_status
                FROM orders
                WHERE length(order_delivery_date) = 10
                  AND substr(order_delivery_date, 7, 4) = ?
                ORDER BY
                    substr(order_delivery_date, 7, 4) || '-' ||
                    substr(order_delivery_date, 4, 2) || '-' ||
                    substr(order_delivery_date, 1, 2) DESC
            ''', (year_str,))
        else:
            # Filter by month and year
            if year is None:
                year = datetime.now().year

            # Parse dates and filter by month/year
            # Date format is DD-MM-YYYY, extract month (positions 4-5) and year (positions 7-10)
            month_str = f"{month:02d}"  # Format month as 2-digit string
            year_str = str(year)

            cursor.execute('''
                SELECT customer_id, customer_name, order_pickup_date, order_delivery_date,
                       bill_amount, bill_id, delivery_status
                FROM orders
                WHERE length(order_delivery_date) = 10
                  AND substr(order_delivery_date, 4, 2) = ?
                  AND substr(order_delivery_date, 7, 4) = ?
                ORDER BY
                    substr(order_delivery_date, 7, 4) || '-' ||
                    substr(order_delivery_date, 4, 2) || '-' ||
                    substr(order_delivery_date, 1, 2) DESC
            ''', (month_str, year_str))
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'customer_id': row['customer_id'],
                'customer_name': row['customer_name'],
                'order_pickup_date': row['order_pickup_date'],
                'order_delivery_date': row['order_delivery_date'],
                'bill_amount': row['bill_amount'],
                'bill_id': row['bill_id'],
                'delivery_status': row['delivery_status']
            })
        
        conn.close()
        return orders
    
    except sqlite3.Error as e:
        conn.close()
        print(f"Database error: {e}")
        return []


def calculate_total_revenue(orders):
    """
    Calculate total revenue from a list of orders.
    
    Args:
        orders (list): List of order dictionaries
    
    Returns:
        float: Total revenue
    """
    return sum(order['bill_amount'] for order in orders)


def get_monthly_report(month=None, year=None):
    """
    Get monthly report with orders and total revenue.
    
    Args:
        month (int): Month number (1-12). If None, returns all orders.
        year (int): Year number. If None, uses current year.
    
    Returns:
        dict: Dictionary containing orders, total_revenue, total_orders, month, year
    """
    orders = get_monthly_orders(month, year)
    total_revenue = calculate_total_revenue(orders)
    
    return {
        'orders': orders,
        'total_revenue': total_revenue,
        'total_orders': len(orders),
        'month': month,
        'year': year if year else datetime.now().year
    }


# Initialize database when module is imported
init_orders_database()
