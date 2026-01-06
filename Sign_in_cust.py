# Software Development project
# Sign-in/Login page for customer
# This module handles customer authentication from HTML form data

import sqlite3
from flask import session

# Database file name
DB_FILE = 'customer_db.sqlite'


def init_database():
    """
    Initialize the SQLite database and create customers table if it doesn't exist.
    Also migrates data from CSV file if database is empty.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create customers table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            cust_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            cust_name TEXT NOT NULL,
            mobile_no TEXT NOT NULL CHECK(length(mobile_no) = 10 AND mobile_no GLOB '[0-9]*'),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


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
    # Initialize database on first use
    init_database()
    
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


def customer_signup(name, username, phone, password):
    """
    Register a new customer in the database.

    Args:
        name (str): Customer's full name
        username (str): Unique username/email
        phone (str): 10-digit phone number
        password (str): Password

    Returns:
        dict: Registration result with 'success' (bool) and 'message' (str)
    """
    # Initialize database on first use
    init_database()

    # Validate inputs
    if not all([name, username, phone, password]):
        return {
            'success': False,
            'message': 'All fields are required.'
        }

    if len(phone) != 10 or not phone.isdigit():
        return {
            'success': False,
            'message': 'Phone number must be exactly 10 digits.'
        }

    if len(password) < 6:
        return {
            'success': False,
            'message': 'Password must be at least 6 characters long.'
        }

    if len(name) < 2 or len(name) > 100:
        return {
            'success': False,
            'message': 'Name must be between 2 and 100 characters.'
        }

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if username already exists
        cursor.execute('SELECT username FROM customers WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return {
                'success': False,
                'message': 'Username already exists. Please choose a different username.'
            }

        # Generate a unique customer ID
        import uuid
        cust_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID

        # Insert new customer
        cursor.execute('''
            INSERT INTO customers (cust_id, username, password, cust_name, mobile_no)
            VALUES (?, ?, ?, ?, ?)
        ''', (cust_id, username, password, name, phone))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'message': 'Account created successfully!',
            'customer_data': {
                'cust_id': cust_id,
                'username': username,
                'cust_name': name,
                'mobile_no': phone
            }
        }

    except sqlite3.Error as e:
        conn.close()
        return {
            'success': False,
            'message': f'Database error: {str(e)}'
        }


def customer_sign_in(request):
    """
    Handle customer sign-in request from HTML form.
    This function extracts username and password from Flask request object,
    validates credentials, and returns the authentication result.

    Args:
        request: Flask request object containing form data

    Returns:
        dict: Authentication result with 'success' (bool) and relevant data/message
    """
    # Get form data from HTML (field names match log_select.html)
    username = request.form.get('loginEmail')  # HTML uses 'loginEmail' as field name
    password = request.form.get('loginPassword')  # HTML uses 'loginPassword' as field name

    # Validate that required fields are provided
    if not username or not password:
        return {
            'success': False,
            'message': 'Username and password are required.'
        }

    # Authenticate the customer
    auth_result = authenticate_customer(username, password)

    # If successful, store customer data in session (optional)
    if auth_result['success'] and 'customer_data' in auth_result:
        # Note: session should be configured in Flask app with app.secret_key
        session['customer_id'] = auth_result['customer_data']['cust_id']
        session['customer_username'] = auth_result['customer_data']['username']
        session['customer_name'] = auth_result['customer_data']['cust_name']
        session['logged_in'] = True

    return auth_result


# Initialize database when module is imported
init_database()
