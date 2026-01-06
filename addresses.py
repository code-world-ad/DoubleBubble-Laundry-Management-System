#!/usr/bin/env python3
"""
Address Management Module for Laundry Management System
Handles customer saved addresses with CRUD operations.
"""

import sqlite3
import os

DB_FILE = 'customer_db.sqlite'

def init_addresses_database():
    """Initialize the addresses table if it doesn't exist"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create addresses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            address_type TEXT NOT NULL DEFAULT 'Home'
                CHECK(address_type IN ('Home', 'Work', 'Other')),
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL CHECK(length(phone) = 10 AND phone GLOB '[0-9]*'),
            address_line1 TEXT NOT NULL,
            address_line2 TEXT,
            city TEXT NOT NULL DEFAULT 'Mumbai',
            state TEXT NOT NULL DEFAULT 'Maharashtra',
            pincode TEXT NOT NULL CHECK(length(pincode) = 6 AND pincode GLOB '[0-9]*'),
            landmark TEXT,
            is_default BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(cust_id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def add_customer_address(customer_id, address_data):
    """
    Add a new address for a customer

    Args:
        customer_id (str): Customer ID
        address_data (dict): Address information

    Returns:
        dict: Success status and message
    """
    init_addresses_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Validate required fields
        required_fields = ['full_name', 'phone', 'address_line1', 'city', 'state', 'pincode']
        for field in required_fields:
            if field not in address_data or not address_data[field] or not address_data[field].strip():
                conn.close()
                return {'success': False, 'message': f'{field.replace("_", " ").title()} is required'}

        # Sanitize inputs
        full_name = address_data['full_name'].strip()[:100]
        phone = address_data['phone'].strip()
        address_line1 = address_data['address_line1'].strip()[:200]
        address_line2 = address_data.get('address_line2', '').strip()[:200]
        city = address_data['city'].strip()[:50]
        state = address_data['state'].strip()[:50]
        pincode = address_data['pincode'].strip()
        landmark = address_data.get('landmark', '').strip()[:100]
        address_type = address_data.get('address_type', 'Home')

        # Validate phone and pincode
        if not phone.isdigit() or len(phone) != 10:
            conn.close()
            return {'success': False, 'message': 'Phone number must be 10 digits'}

        if not pincode.isdigit() or len(pincode) != 6:
            conn.close()
            return {'success': False, 'message': 'Pincode must be 6 digits'}

        # If this is set as default, unset other defaults for this customer
        if address_data.get('is_default'):
            cursor.execute('UPDATE addresses SET is_default = 0 WHERE customer_id = ?', (customer_id,))

        # Insert new address
        cursor.execute('''
            INSERT INTO addresses (customer_id, address_type, full_name, phone, address_line1,
                                 address_line2, city, state, pincode, landmark, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, address_type, full_name, phone, address_line1, address_line2,
              city, state, pincode, landmark, address_data.get('is_default', False)))

        conn.commit()
        address_id = cursor.lastrowid

        conn.close()
        return {'success': True, 'message': 'Address added successfully', 'address_id': address_id}

    except sqlite3.Error as e:
        conn.close()
        return {'success': False, 'message': f'Database error: {str(e)}'}

def get_customer_addresses(customer_id):
    """
    Get all addresses for a customer

    Args:
        customer_id (str): Customer ID

    Returns:
        list: List of address dictionaries
    """
    init_addresses_database()

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT * FROM addresses
            WHERE customer_id = ?
            ORDER BY is_default DESC, created_at DESC
        ''', (customer_id,))

        addresses = []
        for row in cursor.fetchall():
            address = dict(row)
            # Format full address for display
            full_address = f"{address['address_line1']}"
            if address['address_line2']:
                full_address += f", {address['address_line2']}"
            full_address += f", {address['city']}, {address['state']} - {address['pincode']}"
            if address['landmark']:
                full_address += f" (Landmark: {address['landmark']})"

            address['full_address'] = full_address
            addresses.append(address)

        conn.close()
        return addresses

    except sqlite3.Error as e:
        conn.close()
        return []

def update_customer_address(customer_id, address_id, address_data):
    """
    Update an existing address

    Args:
        customer_id (str): Customer ID
        address_id (int): Address ID
        address_data (dict): Updated address information

    Returns:
        dict: Success status and message
    """
    init_addresses_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if address belongs to customer
        cursor.execute('SELECT id FROM addresses WHERE id = ? AND customer_id = ?',
                      (address_id, customer_id))
        if not cursor.fetchone():
            conn.close()
            return {'success': False, 'message': 'Address not found or access denied'}

        # Build update query dynamically
        update_fields = []
        values = []

        field_mappings = {
            'address_type': 'address_type',
            'full_name': 'full_name',
            'phone': 'phone',
            'address_line1': 'address_line1',
            'address_line2': 'address_line2',
            'city': 'city',
            'state': 'state',
            'pincode': 'pincode',
            'landmark': 'landmark',
            'is_default': 'is_default'
        }

        for key, db_field in field_mappings.items():
            if key in address_data:
                update_fields.append(f"{db_field} = ?")
                values.append(address_data[key])

        if not update_fields:
            conn.close()
            return {'success': False, 'message': 'No valid fields to update'}

        # Handle special case for is_default
        if address_data.get('is_default'):
            cursor.execute('UPDATE addresses SET is_default = 0 WHERE customer_id = ?', (customer_id,))

        # Execute update
        query = f"UPDATE addresses SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND customer_id = ?"
        values.extend([address_id, customer_id])

        cursor.execute(query, values)

        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Address updated successfully'}
        else:
            conn.close()
            return {'success': False, 'message': 'Address not found or no changes made'}

    except sqlite3.Error as e:
        conn.close()
        return {'success': False, 'message': f'Database error: {str(e)}'}

def delete_customer_address(customer_id, address_id):
    """
    Delete an address

    Args:
        customer_id (str): Customer ID
        address_id (int): Address ID

    Returns:
        dict: Success status and message
    """
    init_addresses_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM addresses WHERE id = ? AND customer_id = ?',
                      (address_id, customer_id))

        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Address deleted successfully'}
        else:
            conn.close()
            return {'success': False, 'message': 'Address not found or access denied'}

    except sqlite3.Error as e:
        conn.close()
        return {'success': False, 'message': f'Database error: {str(e)}'}

def set_default_address(customer_id, address_id):
    """
    Set an address as the default for a customer

    Args:
        customer_id (str): Customer ID
        address_id (int): Address ID

    Returns:
        dict: Success status and message
    """
    init_addresses_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if address belongs to customer
        cursor.execute('SELECT id FROM addresses WHERE id = ? AND customer_id = ?',
                      (address_id, customer_id))
        if not cursor.fetchone():
            conn.close()
            return {'success': False, 'message': 'Address not found or access denied'}

        # Unset all defaults for this customer
        cursor.execute('UPDATE addresses SET is_default = 0 WHERE customer_id = ?', (customer_id,))

        # Set this address as default
        cursor.execute('UPDATE addresses SET is_default = 1 WHERE id = ? AND customer_id = ?',
                      (address_id, customer_id))

        conn.commit()
        conn.close()
        return {'success': True, 'message': 'Default address updated successfully'}

    except sqlite3.Error as e:
        conn.close()
        return {'success': False, 'message': f'Database error: {str(e)}'}

def get_customer_default_address(customer_id):
    """
    Get the default address for a customer

    Args:
        customer_id (str): Customer ID

    Returns:
        dict or None: Default address or None if no default exists
    """
    init_addresses_database()

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT * FROM addresses
            WHERE customer_id = ? AND is_default = 1
            LIMIT 1
        ''', (customer_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            address = dict(row)
            # Format full address
            full_address = f"{address['address_line1']}"
            if address['address_line2']:
                full_address += f", {address['address_line2']}"
            full_address += f", {address['city']}, {address['state']} - {address['pincode']}"
            if address['landmark']:
                full_address += f" (Landmark: {address['landmark']})"
            address['full_address'] = full_address
            return address
        else:
            return None

    except sqlite3.Error as e:
        conn.close()
        return None

# Initialize the addresses table when module is imported
init_addresses_database()
