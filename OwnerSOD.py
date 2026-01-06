# Owner Status of Delivery module
# Flask-compatible module for managing order delivery status

import sqlite3

# Database file name
DB_FILE = 'customer_db.sqlite'


def init_order_details_database():
    """
    Initialize the SQLite database and create order_details table if it doesn't exist.
    Also migrates data from CSV file if database is empty.
    The table stores combined item and quantity data per order.
    """
    # Import monthrep to ensure orders table exists
    import monthrep
    monthrep.init_orders_database()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create order_details table if it doesn't exist
    # This table combines items and quantities per order (like Flipkart style)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            items_details TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


def get_all_orders(status_filter=None):
    """
    Get all orders from database, optionally filtered by delivery status.
    
    Args:
        status_filter (str): 'Delivered', 'Undelivered', or None for all
    
    Returns:
        list: List of dictionaries containing order information with items
    """
    init_order_details_database()
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Build query based on status filter - aggregate items from order_items table
        if status_filter:
            query = '''
                SELECT o.bill_id, o.customer_id, o.customer_name, o.order_pickup_date,
                       o.order_delivery_date, o.bill_amount, o.delivery_status,
                       GROUP_CONCAT(oi.quantity || 'x ' || oi.item_name, ', ') as items_details
                FROM orders o
                LEFT JOIN order_items oi ON o.bill_id = oi.bill_id
                WHERE o.delivery_status = ?
                GROUP BY o.bill_id, o.customer_id, o.customer_name, o.order_pickup_date,
                         o.order_delivery_date, o.bill_amount, o.delivery_status
                ORDER BY
                    CASE
                        WHEN length(o.order_delivery_date) = 10 AND substr(o.order_delivery_date, 3, 1) = '-' THEN
                            substr(o.order_delivery_date, 7, 4) || '-' ||
                            substr(o.order_delivery_date, 4, 2) || '-' ||
                            substr(o.order_delivery_date, 1, 2)
                        ELSE o.order_delivery_date
                    END DESC
            '''
            cursor.execute(query, (status_filter,))
        else:
            query = '''
                SELECT o.bill_id, o.customer_id, o.customer_name, o.order_pickup_date,
                       o.order_delivery_date, o.bill_amount, o.delivery_status,
                       GROUP_CONCAT(oi.quantity || 'x ' || oi.item_name, ', ') as items_details
                FROM orders o
                LEFT JOIN order_items oi ON o.bill_id = oi.bill_id
                GROUP BY o.bill_id, o.customer_id, o.customer_name, o.order_pickup_date,
                         o.order_delivery_date, o.bill_amount, o.delivery_status
                ORDER BY
                    CASE
                        WHEN length(o.order_delivery_date) = 10 AND substr(o.order_delivery_date, 3, 1) = '-' THEN
                            substr(o.order_delivery_date, 7, 4) || '-' ||
                            substr(o.order_delivery_date, 4, 2) || '-' ||
                            substr(o.order_delivery_date, 1, 2)
                        ELSE o.order_delivery_date
                    END DESC
            '''
            cursor.execute(query)

        orders = []
        for row in cursor.fetchall():
            orders.append({
                'bill_id': row['bill_id'],
                'customer_id': row['customer_id'],
                'customer_name': row['customer_name'],
                'order_pickup_date': row['order_pickup_date'],
                'order_delivery_date': row['order_delivery_date'],
                'bill_amount': row['bill_amount'],
                'delivery_status': row['delivery_status'],
                'items_details': row['items_details'] if row['items_details'] else 'No items'
            })
        
        conn.close()
        return orders
    
    except sqlite3.Error as e:
        conn.close()
        print(f"Database error: {e}")
        return []


def get_order_details(bill_id):
    """
    Get detailed information for a specific order.
    
    Args:
        bill_id (str): The bill ID of the order
    
    Returns:
        dict: Dictionary containing order details or None if not found
    """
    init_order_details_database()
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT o.bill_id, o.customer_id, o.customer_name, o.pickup_address, o.delivery_address,
                   o.order_pickup_date, o.order_delivery_date, o.bill_amount, o.delivery_status,
                   GROUP_CONCAT(oi.quantity || 'x ' || oi.item_name, ', ') as items_details
            FROM orders o
            LEFT JOIN order_items oi ON o.bill_id = oi.bill_id
            WHERE o.bill_id = ?
            GROUP BY o.bill_id, o.customer_id, o.customer_name, o.pickup_address, o.delivery_address,
                     o.order_pickup_date, o.order_delivery_date, o.bill_amount, o.delivery_status
        ''', (bill_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
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
                'items_details': row['items_details'] if row['items_details'] else 'No items'
            }
        return None
    
    except sqlite3.Error as e:
        conn.close()
        print(f"Database error: {e}")
        return None


def update_delivery_status(bill_id, status, cancelled_by=None):
    """
    Update the delivery status of an order.

    Args:
        bill_id (str): The bill ID of the order
        status (str): Delivery status ('Delivered', 'Undelivered', 'Cancelled')
        cancelled_by (str): Who cancelled the order ('customer' or None)

    Returns:
        bool: True if update was successful, False otherwise
    """
    init_order_details_database()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        if status == 'Cancelled' and cancelled_by:
            cursor.execute('''
                UPDATE orders
                SET delivery_status = ?, cancelled_by = ?
                WHERE bill_id = ?
            ''', (status, cancelled_by, bill_id))
        else:
            cursor.execute('''
                UPDATE orders
                SET delivery_status = ?
                WHERE bill_id = ?
            ''', (status, bill_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    except sqlite3.Error as e:
        conn.close()
        print(f"Database error: {e}")
        return False


# Initialize database when module is imported
init_order_details_database()
