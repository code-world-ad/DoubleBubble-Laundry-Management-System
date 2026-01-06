# Customer Status of Delivery module
# Flask-compatible module for customers to view their order delivery status

import sqlite3
import csv
import os
from datetime import datetime

# Database file name
DB_FILE = 'customer_db.sqlite'


def get_customer_orders(customer_id=None, month=None, year=None):
    """
    Get orders from database for a specific customer, optionally filtered by month and year.
    Orders are returned in descending order of delivery date.

    Args:
        customer_id (str): The customer ID to filter by
        month (int): Month number (1-12). If None, returns all orders.
        year (int): Year number. If None, uses current year.

    Returns:
        list: List of dictionaries containing order information
    """
    try:
        # Import cart module to ensure all tables are initialized
        import Manipulation_of_cart_edited
        Manipulation_of_cart_edited.init_cart_database()

        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Simple query to get all orders for customer
        query = '''
            SELECT bill_id, customer_id, customer_name, order_pickup_date,
                   order_delivery_date, bill_amount, delivery_status
            FROM orders
            WHERE customer_id = ?
            ORDER BY order_delivery_date DESC
        '''

        cursor.execute(query, (customer_id,))
        rows = cursor.fetchall()

        orders = []
        for row in rows:
            bill_id = row['bill_id']

            # Get items for this order
            try:
                cursor.execute('''
                    SELECT item_name, quantity, unit_price, total_price
                    FROM order_items
                    WHERE bill_id = ?
                    ORDER BY item_name
                ''', (bill_id,))

                items_rows = cursor.fetchall()
                # Convert sqlite3.Row objects to dictionaries
                items = [dict(row) for row in items_rows]
                items_details = ', '.join([f"{item['quantity']}x {item['item_name']}" for item in items]) if items else 'No items'
            except Exception as e:
                print(f"Error getting items for {bill_id}: {e}")
                items = []
                items_details = 'No items'

            orders.append({
                'bill_id': row['bill_id'],
                'customer_id': row['customer_id'],
                'customer_name': row['customer_name'],
                'order_pickup_date': row['order_pickup_date'],
                'order_delivery_date': row['order_delivery_date'],
                'bill_amount': row['bill_amount'],
                'delivery_status': row['delivery_status'],
                'items_details': items_details,
                'items': items
            })

        conn.close()
        return orders

    except Exception as e:
        print(f"Error in get_customer_orders: {e}")
        return []


def get_order_details_for_customer(bill_id, customer_id):
    """
    Get detailed information for a specific order, ensuring it belongs to the customer.

    Args:
        bill_id (str): The bill ID of the order
        customer_id (str): The customer ID for security check

    Returns:
        dict: Dictionary containing order details or None if not found/not authorized
    """
    # Import monthrep to ensure database is initialized
    import Manipulation_of_cart_edited
    Manipulation_of_cart_edited.init_cart_database()

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get order details with security check
        cursor.execute('''
            SELECT o.bill_id, o.customer_id, o.customer_name, o.pickup_address, o.delivery_address,
                   o.order_pickup_date, o.order_delivery_date, o.bill_amount, o.delivery_status
            FROM orders o
            WHERE o.bill_id = ? AND o.customer_id = ?
        ''', (bill_id, customer_id))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # Get items for this order using a separate connection
        conn2 = sqlite3.connect(DB_FILE)
        conn2.row_factory = sqlite3.Row
        cursor2 = conn2.cursor()
        cursor2.execute('''
            SELECT item_name, quantity, unit_price, total_price
            FROM order_items
            WHERE bill_id = ?
            ORDER BY item_name
        ''', (bill_id,))

        items_rows = cursor2.fetchall()
        # Convert sqlite3.Row objects to dictionaries
        items = [dict(row) for row in items_rows]
        items_details = ', '.join([f"{item['quantity']}x {item['item_name']}" for item in items]) if items else 'No items'

        cursor2.close()
        conn2.close()
        conn.close()

        return {
            'bill_id': row['bill_id'],
            'customer_id': row['customer_id'],
            'customer_name': row['customer_name'],
            'pickup_address': row['pickup_address'],
            'delivery_address': row['delivery_address'],
            'order_pickup_date': row['order_pickup_date'],
            'order_delivery_date': row['order_delivery_date'],
            'bill_amount': row['bill_amount'],
            'delivery_status': row['delivery_status'],
            'items_details': items_details,
            'items': items  # Individual items for bill generation
        }

    except sqlite3.Error as e:
        conn.close()
        print(f"Database error: {e}")
        return None


def get_customer_statistics(customer_id):
    """
    Get statistics for a customer including total orders, delivered orders, pending orders, etc.

    Args:
        customer_id (str): The customer ID

    Returns:
        dict: Dictionary containing customer statistics
    """
    # Import monthrep to ensure database is initialized
    import Manipulation_of_cart_edited
    Manipulation_of_cart_edited.init_cart_database()

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get total orders
        cursor.execute('SELECT COUNT(*) FROM orders WHERE customer_id = ?', (customer_id,))
        total_orders = cursor.fetchone()[0]

        # Get delivered orders
        cursor.execute('SELECT COUNT(*) FROM orders WHERE customer_id = ? AND delivery_status = "Delivered"', (customer_id,))
        delivered_orders = cursor.fetchone()[0]

        # Get undelivered orders
        cursor.execute('SELECT COUNT(*) FROM orders WHERE customer_id = ? AND delivery_status = "Undelivered"', (customer_id,))
        undelivered_orders = cursor.fetchone()[0]

        # Get total amount spent
        cursor.execute('SELECT SUM(bill_amount) FROM orders WHERE customer_id = ?', (customer_id,))
        total_amount = cursor.fetchone()[0] or 0

        conn.close()

        return {
            'total_orders': total_orders,
            'delivered_orders': delivered_orders,
            'undelivered_orders': undelivered_orders,
            'total_amount': total_amount
        }

    except sqlite3.Error as e:
        conn.close()
        print(f"Database error: {e}")
        return {
            'total_orders': 0,
            'delivered_orders': 0,
            'undelivered_orders': 0,
            'total_amount': 0
        }