# This module has been updated to work with SQLite database instead of CSV files
# It provides a simple authentication function for customers

import sqlite3

# Database file name
DB_FILE = 'customer_db.sqlite'

def authenticate_customer(username, password):
    """
    Authenticate a customer by checking username and password in the database.

    Args:
        username (str): The customer's username
        password (str): The customer's password

    Returns:
        dict: Dictionary with 'success' (bool) and 'customer_data' (dict) or 'message' (str)
              If successful, customer_data contains: cust_id, username, cust_name, mobile_no
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # This allows column access by name
    cursor = conn.cursor()

    try:
        # Query the database for the customer with matching username and password
        cursor.execute('''
            SELECT cust_id, username, password, cust_name, mobile_no
            FROM customers
            WHERE username = ? AND password = ?
        ''', (username, password))

        customer = cursor.fetchone()

        if customer:
            # Customer exists and credentials are correct
            customer_data = {
                'cust_id': customer['cust_id'],
                'username': customer['username'],
                'cust_name': customer['cust_name'],
                'mobile_no': customer['mobile_no']
            }
            conn.close()
            return {
                'success': True,
                'customer_data': customer_data,
                'message': 'Login successful!'
            }
        else:
            # Check if username exists but password is wrong
            cursor.execute('SELECT username FROM customers WHERE username = ?', (username,))
            if cursor.fetchone():
                conn.close()
                return {
                    'success': False,
                    'message': 'Invalid password. Please check your credentials.'
                }
            else:
                conn.close()
                return {
                    'success': False,
                    'message': 'Customer not found. Please check your username.'
                }

    except sqlite3.Error as e:
        conn.close()
        return {
            'success': False,
            'message': f'Database error: {str(e)}'
        }

# Legacy Tkinter code removed - this module now only provides database authentication functions