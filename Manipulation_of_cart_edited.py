# Laundry Cart Management Module
# Flask-compatible module for managing customer laundry carts and orders

import sqlite3
import csv
import os
from datetime import datetime, timedelta
from flask import session

# Database file name
DB_FILE = 'customer_db.sqlite'
ORDER_DETAILS_CSV = 'cust_order_details.csv'

# Item costs
ITEM_COSTS = {
    'Shirt': 15,
    'Pant': 20,
    'Suit': 25,
    'Socks': 10,
    'Dress': 20,
    'Jeans': 21,
    'T-shirt': 12
}


def init_cart_database():
    """
    Initialize the SQLite database and create cart table if it doesn't exist.
    """
    # Import monthrep to ensure orders table exists
    import monthrep
    monthrep.init_orders_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create cart table for temporary cart items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            total_price REAL NOT NULL CHECK(total_price >= 0),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(cust_id)
        )
    ''')

    # Create order_items table for finalized orders (more detailed than order_details)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            total_price REAL NOT NULL CHECK(total_price >= 0),
            FOREIGN KEY (bill_id) REFERENCES orders(bill_id)
        )
    ''')

    conn.commit()
    conn.close()


def add_to_cart(customer_id, item_name, quantity):
    """
    Add item to customer's cart.

    Args:
        customer_id (str): Customer ID
        item_name (str): Name of the item
        quantity (int): Quantity to add

    Returns:
        dict: Success status and message
    """
    if item_name not in ITEM_COSTS:
        return {'success': False, 'message': 'Invalid item selected'}

    if quantity <= 0:
        return {'success': False, 'message': 'Quantity must be greater than 0'}

    init_cart_database()

    unit_price = ITEM_COSTS[item_name]
    total_price = unit_price * quantity

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if item already exists in cart
        cursor.execute('''
            SELECT id, quantity, total_price FROM cart
            WHERE customer_id = ? AND item_name = ?
        ''', (customer_id, item_name))

        existing_item = cursor.fetchone()

        if existing_item:
            # Update existing item
            new_quantity = existing_item[1] + quantity
            new_total = unit_price * new_quantity
            cursor.execute('''
                UPDATE cart
                SET quantity = ?, total_price = ?, added_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_quantity, new_total, existing_item[0]))
        else:
            # Add new item
            cursor.execute('''
                INSERT INTO cart (customer_id, item_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_id, item_name, quantity, unit_price, total_price))

        conn.commit()
        conn.close()

        return {'success': True, 'message': f'{item_name} added to cart successfully'}

    except sqlite3.Error as e:
        conn.close()
        return {'success': False, 'message': f'Database error: {str(e)}'}


def get_cart_items(customer_id):
    """
    Get all items in customer's cart.

    Args:
        customer_id (str): Customer ID

    Returns:
        list: List of cart items with item details
    """
    init_cart_database()

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT item_name, quantity, unit_price, total_price, added_at
            FROM cart
            WHERE customer_id = ?
            ORDER BY added_at DESC
        ''', (customer_id,))

        items = []
        for row in cursor.fetchall():
            items.append({
                'item_name': row['item_name'],
                'quantity': row['quantity'],
                'unit_price': row['unit_price'],
                'total_price': row['total_price'],
                'added_at': row['added_at']
            })

        conn.close()
        return items

    except sqlite3.Error as e:
        conn.close()
        return []


def update_cart_item(customer_id, item_name, new_quantity):
    """
    Update quantity of an item in cart.

    Args:
        customer_id (str): Customer ID
        item_name (str): Item name
        new_quantity (int): New quantity

    Returns:
        dict: Success status and message
    """
    if new_quantity <= 0:
        return remove_from_cart(customer_id, item_name)

    init_cart_database()

    unit_price = ITEM_COSTS.get(item_name)
    if not unit_price:
        return {'success': False, 'message': 'Invalid item'}

    new_total = unit_price * new_quantity

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE cart
            SET quantity = ?, total_price = ?, added_at = CURRENT_TIMESTAMP
            WHERE customer_id = ? AND item_name = ?
        ''', (new_quantity, new_total, customer_id, item_name))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if success:
            return {'success': True, 'message': f'{item_name} quantity updated'}
        else:
            return {'success': False, 'message': 'Item not found in cart'}

    except sqlite3.Error as e:
        conn.close()
        return {'success': False, 'message': f'Database error: {str(e)}'}


def remove_from_cart(customer_id, item_name):
    """
    Remove item from cart.

    Args:
        customer_id (str): Customer ID
        item_name (str): Item name

    Returns:
        dict: Success status and message
    """
    init_cart_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            DELETE FROM cart
            WHERE customer_id = ? AND item_name = ?
        ''', (customer_id, item_name))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if success:
            return {'success': True, 'message': f'{item_name} removed from cart'}
        else:
            return {'success': False, 'message': 'Item not found in cart'}

    except sqlite3.Error as e:
        conn.close()
        return {'success': False, 'message': f'Database error: {str(e)}'}


def clear_cart(customer_id):
    """
    Clear all items from customer's cart.

    Args:
        customer_id (str): Customer ID

    Returns:
        dict: Success status and message
    """
    init_cart_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM cart WHERE customer_id = ?', (customer_id,))
        conn.commit()
        conn.close()

        return {'success': True, 'message': 'Cart cleared successfully'}

    except sqlite3.Error as e:
        conn.close()
        return {'success': False, 'message': f'Database error: {str(e)}'}


def get_cart_total(customer_id):
    """
    Get total cost of items in cart.

    Args:
        customer_id (str): Customer ID

    Returns:
        float: Total cost
    """
    init_cart_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT SUM(total_price) FROM cart WHERE customer_id = ?
        ''', (customer_id,))

        total = cursor.fetchone()[0] or 0
        conn.close()
        return float(total)

    except sqlite3.Error:
        conn.close()
        return 0


def calculate_delivery_date(pickup_date_str):
    """
    Calculate delivery date based on current active orders (not delivered).

    Args:
        pickup_date_str (str): Pickup date in DD-MM-YYYY format

    Returns:
        str: Delivery date in DD-MM-YYYY format
    """
    # Import OwnerSOD to check active orders count
    import OwnerSOD

    # Get all orders that are not yet delivered (active orders)
    active_orders = OwnerSOD.get_all_orders(None)  # Get all orders
    undelivered_count = sum(1 for order in active_orders
                           if order['delivery_status'] != 'Delivered')

    # Parse pickup date
    pickup_date = datetime.strptime(pickup_date_str, '%d-%m-%Y').date()

    # Calculate delivery date based on active order count
    if undelivered_count < 5:
        delivery_date = pickup_date + timedelta(days=1)
    else:
        delivery_date = pickup_date + timedelta(days=2)

    return delivery_date.strftime('%d-%m-%Y')


def place_order(customer_id, pickup_date_str, pickup_address, delivery_address):
    """
    Place order from cart items and calculate delivery date.

    Args:
        customer_id (str): Customer ID
        pickup_date_str (str): Pickup date in DD-MM-YYYY format
        pickup_address (str): Address for pickup
        delivery_address (str): Address for delivery

    Returns:
        dict: Order details and success status
    """
    init_cart_database()

    # Get customer info
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Get customer name
        cursor.execute('SELECT cust_name FROM customers WHERE cust_id = ?', (customer_id,))
        customer_row = cursor.fetchone()
        if not customer_row:
            conn.close()
            return {'success': False, 'message': 'Customer not found'}

        customer_name = customer_row[0]

        # Get cart items
        cart_items = get_cart_items(customer_id)
        if not cart_items:
            conn.close()
            return {'success': False, 'message': 'Cart is empty'}

        # Calculate total (subtotal)
        subtotal_amount = get_cart_total(customer_id)

        # Calculate GST (18%)
        gst_rate = 0.18
        gst_amount = round(subtotal_amount * gst_rate, 2)
        final_bill_amount = round(subtotal_amount + gst_amount, 2)

        # Calculate delivery date
        delivery_date_str = calculate_delivery_date(pickup_date_str)

        # Generate bill ID
        cursor.execute('SELECT COUNT(*) FROM orders')
        order_count = cursor.fetchone()[0]
        bill_id = f'B{order_count + 1:03d}'

        # Validate addresses
        if not pickup_address or not pickup_address.strip():
            conn.close()
            return {'success': False, 'message': 'Pickup address is required'}

        if not delivery_address or not delivery_address.strip():
            conn.close()
            return {'success': False, 'message': 'Delivery address is required'}

        # Sanitize addresses (remove potentially harmful characters)
        pickup_address = pickup_address.strip()[:500]  # Limit length
        delivery_address = delivery_address.strip()[:500]  # Limit length

        # Create order record
        cursor.execute('''
            INSERT INTO orders (customer_id, customer_name, pickup_address, delivery_address,
                              order_pickup_date, order_delivery_date, bill_amount, bill_id, delivery_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, customer_name, pickup_address, delivery_address, pickup_date_str,
              delivery_date_str, final_bill_amount, bill_id, 'Order Placed'))

        # Move cart items to order_items table
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (bill_id, item_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (bill_id, item['item_name'], item['quantity'],
                  item['unit_price'], item['total_price']))

        # Clear cart
        cursor.execute('DELETE FROM cart WHERE customer_id = ?', (customer_id,))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'message': 'Order placed successfully!',
            'order_details': {
                'bill_id': bill_id,
                'customer_name': customer_name,
                'pickup_date': pickup_date_str,
                'delivery_date': delivery_date_str,
                'total_amount': final_bill_amount,
                'subtotal_amount': subtotal_amount,
                'gst_amount': gst_amount,
                'items': cart_items
            }
        }

    except sqlite3.Error as e:
        conn.close()
        return {'success': False, 'message': f'Database error: {str(e)}'}


def get_available_pickup_dates():
    """
    Get available pickup dates (today + next 10 days).

    Returns:
        list: List of available dates in DD-MM-YYYY format
    """
    dates = []
    today = datetime.now().date()

    for i in range(11):  # Today + 10 days
        date = today + timedelta(days=i)
        dates.append(date.strftime('%d-%m-%Y'))

    return dates


# Initialize database when module is imported
init_cart_database()
