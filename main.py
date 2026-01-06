import Sign_in_cust as ctsign
import Log_in_Owner as ownlogin
import Log_in_cust as ctlogin
import monthrep
import OwnerSOD
import CustSOD
import Manipulation_of_cart_edited as cart_module
import addresses

from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Required for session management

users = {
    "customer": {"username": "customer123", "password": "custpass"},
    "owner": {"username": "owner123", "password": "ownpass"},
}

signups = []


@app.route('/')
def home():
    return render_template('Home Page.html')

@app.route('/log_select')
def login_page():
    return render_template('General Login.html')

@app.route('/login', methods=['POST'])
def login():
    auth_option = request.form.get("authOption")
    
    if auth_option == "login":
        # Use the Sign_in_cust module for customer authentication
        auth_result = ctsign.customer_sign_in(request)

        if auth_result['success']:
            # Return JSON response that matches HTML JavaScript expectations
            return jsonify({'login_status': 1, 'message': 'Customer login successful!'})
        else:
            # Return JSON response for failed login
            return jsonify({'login_status': 0, 'message': auth_result.get('message', 'Login failed. Please check your credentials.')})
    
    elif auth_option == "ownlogin":
        # Use the Log_in_Owner module for owner authentication
        auth_result = ownlogin.owner_sign_in(request)

        if auth_result['success']:
            # Return JSON response that matches HTML JavaScript expectations
            return jsonify({'login_status': 1, 'message': 'Owner login successful!'})
        else:
            # Return JSON response for failed login
            return jsonify({'login_status': 0, 'message': auth_result.get('message', 'Owner login failed. Please check your credentials.')})


@app.route('/signup', methods=['POST'])
def signup():
    try:
        # Handle JSON data from frontend
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400

        name = data.get('name')
        username = data.get('username')
        phone = data.get('phone')
        password = data.get('password')

        # Use the signup function from Sign_in_cust module
        signup_result = ctsign.customer_signup(name, username, phone, password)

        if signup_result['success']:
            # Set session variables for the newly created user
            session['customer_id'] = signup_result['customer_data']['cust_id']
            session['customer_username'] = signup_result['customer_data']['username']
            session['customer_name'] = signup_result['customer_data']['cust_name']
            session['logged_in'] = True

            return jsonify({
                'success': True,
                'message': signup_result['message']
            })
        else:
            return jsonify({
                'success': False,
                'message': signup_result['message']
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


@app.route('/cust_home_page')
def customer_home():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('cust_home_page.html')


@app.route('/laundry_cart')
def laundry_cart():
    # Check if customer is logged in
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('Laundry Cart.html')


@app.route('/customer_delivery_status')
def customer_delivery_status():
    # Check if customer is logged in
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('DeliveryStatusCust.html')


@app.route('/api/customer/orders', methods=['GET'])
def get_customer_orders():
    try:
        # Check if customer is logged in
        if not session.get('logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401

        customer_id = session.get('customer_id')
        if not customer_id:
            return jsonify({'error': 'Customer ID not found'}), 401

        # Get month and year from query parameters
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)

        # Get customer orders
        orders = CustSOD.get_customer_orders(customer_id, month, year)

        return jsonify({'orders': orders})
    except Exception as e:
        print(f"Error in get_customer_orders: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/customer/order/<bill_id>', methods=['GET'])
def get_customer_order_details(bill_id):
    # Check if customer is logged in
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Customer ID not found'}), 401

    # Get order details (with security check that it belongs to the customer)
    order_details = CustSOD.get_order_details_for_customer(bill_id, customer_id)

    if order_details:
        return jsonify(order_details)
    else:
        return jsonify({'error': 'Order not found'}), 404


@app.route('/api/customer/stats', methods=['GET'])
def get_customer_stats():
    # Check if customer is logged in
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Customer ID not found'}), 401

    # Get customer statistics
    stats = CustSOD.get_customer_statistics(customer_id)

    return jsonify(stats)


@app.route('/own_home_page')
def owner_home():
    # Check if owner is logged in
    if not session.get('owner_logged_in'):
        return redirect(url_for('login_page'))
    return render_template('own_home.html')

@app.route('/generate_orders', methods=['POST'])
def generate_orders():
    month = request.json.get('month')
    if not month or not (1 <= int(month) <= 12):
        return flash({"error": "Invalid month. Please enter a value between 1 and 12."}), 400
    
    # Backend logic for generating orders
    # Example: Generate orders for the given month
    orders = f"Orders for month {month} generated successfully."
    return flash({"message": orders})

@app.route('/report')
def report_page():
    # Check if owner is logged in
    if not session.get('owner_logged_in'):
        return redirect(url_for('login_page'))
    return render_template('report.html')


@app.route('/monthly_report', methods=['GET'])
def monthly_report():
    # Check if owner is logged in
    if not session.get('owner_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get month and year from query parameters
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    # Get monthly report data
    report_data = monthrep.get_monthly_report(month, year)
    
    return jsonify(report_data)


@app.route('/own_sod.html')
def owner_sod_page():
    # Check if owner is logged in
    if not session.get('owner_logged_in'):
        return redirect(url_for('login_page'))
    return render_template('own_sod.html')


@app.route('/api/orders', methods=['GET'])
def get_orders():
    # Check if owner is logged in
    if not session.get('owner_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get status filter from query parameters
    status_filter = request.args.get('status')  # 'Delivered', 'Undelivered', or None
    
    # Get orders from database
    orders = OwnerSOD.get_all_orders(status_filter)
    
    return jsonify({'orders': orders})


@app.route('/api/order/<bill_id>', methods=['GET'])
def get_order_details(bill_id):
    # Check if owner is logged in
    if not session.get('owner_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get order details from database
    order_details = OwnerSOD.get_order_details(bill_id)
    
    if order_details:
        return jsonify(order_details)
    else:
        return jsonify({'error': 'Order not found'}), 404


@app.route('/api/order/<bill_id>/status', methods=['PUT'])
def update_order_status(bill_id):
    # Check if owner is logged in
    if not session.get('owner_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get status from request body
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['Order Placed', 'Order Picked', 'In Process', 'Out for Delivery', 'Delivered', 'Cancelled']:
        return jsonify({'error': 'Invalid status. Must be one of: Order Placed, Order Picked, In Process, Out for Delivery, Delivered, Cancelled'}), 400
    
    # Update order status
    success = OwnerSOD.update_delivery_status(bill_id, status)
    
    if success:
        return jsonify({'message': 'Order status updated successfully'})
    else:
        return jsonify({'error': 'Order not found or update failed'}), 404


# Cart API routes
@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    # Check if customer is logged in
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    data = request.get_json()
    item_name = data.get('item_name')
    quantity = int(data.get('quantity', 0))

    if not item_name or quantity <= 0:
        return jsonify({'success': False, 'message': 'Invalid item or quantity'}), 400

    result = cart_module.add_to_cart(customer_id, item_name, quantity)
    return jsonify(result)


@app.route('/api/cart/items', methods=['GET'])
def get_cart_items():
    # Check if customer is logged in
    if not session.get('logged_in'):
        return jsonify({'items': []}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'items': []}), 401

    items = cart_module.get_cart_items(customer_id)
    return jsonify({'items': items})


@app.route('/api/cart/remove/<item_name>', methods=['DELETE'])
def remove_from_cart(item_name):
    # Check if customer is logged in
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    result = cart_module.remove_from_cart(customer_id, item_name)
    return jsonify(result)


@app.route('/api/cart/pickup-dates', methods=['GET'])
def get_pickup_dates():
    dates = cart_module.get_available_pickup_dates()
    return jsonify(dates)


@app.route('/api/cart/place-order', methods=['POST'])
def place_order():
    # Check if customer is logged in
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    data = request.get_json()
    pickup_date = data.get('pickup_date')
    pickup_address = data.get('pickup_address')
    delivery_address = data.get('delivery_address')

    if not pickup_date:
        return jsonify({'success': False, 'message': 'Pickup date is required'}), 400

    if not pickup_address:
        return jsonify({'success': False, 'message': 'Pickup address is required'}), 400

    if not delivery_address:
        return jsonify({'success': False, 'message': 'Delivery address is required'}), 400

    result = cart_module.place_order(customer_id, pickup_date, pickup_address, delivery_address)
    return jsonify(result)


@app.route('/api/generate-bill/<bill_id>', methods=['GET'])
def generate_bill(bill_id):
    try:
        # Check if customer is logged in
        if not session.get('logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401

        customer_id = session.get('customer_id')
        if not customer_id:
            return jsonify({'error': 'Customer ID not found'}), 401

        # Get order details with items
        order_details = CustSOD.get_order_details_for_customer(bill_id, customer_id)

        if not order_details:
            return jsonify({'error': 'Order not found'}), 404

        # Generate HTML bill content
        bill_html = generate_bill_html(order_details)

        return jsonify({
            'bill_html': bill_html,
            'bill_id': bill_id
        })
    except Exception as e:
        print(f"Error generating bill: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def generate_bill_html(order_details):
    """Generate HTML content for the bill"""
    items_html = ""
    subtotal = 0

    for item in order_details['items']:
        # Convert sqlite3.Row to dict if needed
        if hasattr(item, 'keys'):
            item_dict = dict(item)
        else:
            item_dict = item

        item_total = float(item_dict['total_price'])
        subtotal += item_total

        items_html += f"""
        <tr>
            <td>{item_dict['item_name']}</td>
            <td style="text-align: center;">{item_dict['quantity']}</td>
            <td style="text-align: right;">₹{float(item_dict['unit_price']):.2f}</td>
            <td style="text-align: right;">₹{item_total:.2f}</td>
        </tr>
        """

    # Calculate totals
    total_amount = float(order_details['bill_amount'])

    bill_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laundry Bill - {order_details['bill_id']}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
                color: #333;
            }}
            .bill-container {{
                max-width: 700px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .bill-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .bill-header h1 {{
                margin: 0 0 10px 0;
                font-size: 32px;
                font-weight: bold;
            }}
            .bill-header .subtitle {{
                margin: 0;
                font-size: 16px;
                opacity: 0.9;
            }}
            .bill-header .bill-id {{
                margin-top: 15px;
                font-size: 18px;
                font-weight: bold;
                background: rgba(255,255,255,0.2);
                padding: 8px 16px;
                border-radius: 20px;
                display: inline-block;
            }}
            .bill-body {{
                padding: 30px;
            }}
            .bill-info {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }}
            .info-section {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
            }}
            .info-section h3 {{
                margin: 0 0 15px 0;
                color: #667eea;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .info-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                padding-bottom: 8px;
                border-bottom: 1px solid #dee2e6;
            }}
            .info-row:last-child {{
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }}
            .info-row strong {{
                color: #495057;
            }}
            .status-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            .status-delivered {{ background: #d4edda; color: #155724; }}
            .status-order-placed {{ background: #cce5ff; color: #004085; }}
            .status-in-process {{ background: #e2e3e5; color: #383d41; }}
            .status-out-for-delivery {{ background: #fff3cd; color: #856404; }}
            .status-order-picked {{ background: #d1ecf1; color: #0c5460; }}
            .items-section {{
                margin-bottom: 30px;
            }}
            .items-section h3 {{
                margin: 0 0 20px 0;
                color: #667eea;
                font-size: 18px;
                text-align: center;
            }}
            .items-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                overflow: hidden;
            }}
            .items-table th {{
                background: #667eea;
                color: white;
                padding: 15px 12px;
                text-align: left;
                font-weight: bold;
                border-bottom: 2px solid #dee2e6;
            }}
            .items-table td {{
                padding: 15px 12px;
                border-bottom: 1px solid #dee2e6;
                background: #fff;
            }}
            .items-table tr:nth-child(even) td {{
                background: #f8f9fa;
            }}
            .items-table tr:hover td {{
                background: #e9ecef;
            }}
            .total-section {{
                background: #f8f9fa;
                border: 2px solid #667eea;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
            }}
            .total-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 18px;
                font-weight: bold;
                color: #495057;
                margin-bottom: 10px;
            }}
            .grand-total {{
                font-size: 24px;
                color: #667eea;
                border-top: 2px solid #667eea;
                padding-top: 15px;
                margin-top: 15px;
            }}
            .bill-footer {{
                background: #667eea;
                color: white;
                padding: 25px 30px;
                text-align: center;
                margin-top: 30px;
            }}
            .bill-footer h4 {{
                margin: 0 0 10px 0;
                font-size: 18px;
            }}
            .contact-info {{
                display: flex;
                justify-content: center;
                gap: 30px;
                flex-wrap: wrap;
            }}
            .contact-item {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            @media print {{
                body {{
                    background: white !important;
                    padding: 0 !important;
                }}
                .bill-container {{
                    box-shadow: none !important;
                    margin: 0 !important;
                }}
                .no-print {{
                    display: none !important;
                }}
            }}
            @media (max-width: 600px) {{
                .bill-info {{
                    grid-template-columns: 1fr;
                }}
                .contact-info {{
                    flex-direction: column;
                    gap: 10px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="bill-container">
            <div class="bill-header">
                <h1>🧺 DoubleBubble Laundry</h1>
                <p class="subtitle">Professional Laundry & Dry Cleaning Services</p>
                <div class="bill-id">Bill #{order_details['bill_id']}</div>
            </div>

            <div class="bill-body">
                <div class="bill-info">
                    <div class="info-section">
                        <h3>Customer Details</h3>
                        <div class="info-row">
                            <strong>Name:</strong>
                            <span>{order_details['customer_name']}</span>
                        </div>
                        <div class="info-row">
                            <strong>Customer ID:</strong>
                            <span>{order_details['customer_id']}</span>
                        </div>
                    </div>

                    <div class="info-section">
                        <h3>Order Details</h3>
                        <div class="info-row">
                            <strong>Pickup Date:</strong>
                            <span>{order_details.get('order_pickup_date', 'N/A')}</span>
                        </div>
                        <div class="info-row">
                            <strong>Delivery Date:</strong>
                            <span>{order_details.get('order_delivery_date', 'N/A')}</span>
                        </div>
                        <div class="info-row">
                            <strong>Status:</strong>
                            <span class="status-badge status-{order_details['delivery_status'].lower().replace(' ', '-')}">{order_details['delivery_status']}</span>
                        </div>
                    </div>
                </div>

                <div class="items-section">
                    <h3>Laundry Items</h3>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th>Item Description</th>
                                <th style="text-align: center;">Quantity</th>
                                <th style="text-align: right;">Rate (₹)</th>
                                <th style="text-align: right;">Amount (₹)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>

                    <div class="total-section">
                        <div class="total-row">
                            <span>Subtotal:</span>
                            <span>₹{subtotal:.2f}</span>
                        </div>
                        <div class="total-row">
                            <span>GST (18%):</span>
                            <span>₹{(subtotal * 0.18):.2f}</span>
                        </div>
                        <div class="total-row grand-total">
                            <span>Total Amount:</span>
                            <span>₹{total_amount:.2f}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bill-footer">
                <h4>Thank you for choosing DoubleBubble Laundry Services!</h4>
                <div class="contact-info">
                    <div class="contact-item">
                        <span>📞</span>
                        <span>+91-9876543210</span>
                    </div>
                    <div class="contact-item">
                        <span>📧</span>
                        <span>info@doublebubble.com</span>
                    </div>
                    <div class="contact-item">
                        <span>🌐</span>
                        <span>www.doublebubble.com</span>
                    </div>
                </div>
                <p style="margin-top: 15px; font-size: 12px; opacity: 0.8;">
                    This is a computer-generated bill. No signature required.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return bill_html


@app.route('/api/cancel-order/<bill_id>', methods=['POST'])
def cancel_order(bill_id):
    # Check if customer is logged in
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    # Check if order exists and belongs to customer and is in cancellable state
    order_details = CustSOD.get_order_details_for_customer(bill_id, customer_id)

    if not order_details:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    # Only allow cancellation if order is in "Order Placed" status
    if order_details['delivery_status'] != 'Order Placed':
        return jsonify({'success': False, 'message': 'Order cannot be cancelled at this stage'}), 400

    # Update order status to cancelled by customer
    import OwnerSOD
    success = OwnerSOD.update_delivery_status(bill_id, 'Cancelled', 'customer')

    if success:
        return jsonify({'success': True, 'message': 'Order cancelled successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to cancel order'}), 500


# ==================== ADDRESS MANAGEMENT API ENDPOINTS ====================

@app.route('/api/addresses', methods=['GET'])
def get_customer_addresses():
    """Get all addresses for the logged-in customer"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    addresses_list = addresses.get_customer_addresses(customer_id)
    return jsonify({'success': True, 'addresses': addresses_list})


@app.route('/api/addresses', methods=['POST'])
def add_customer_address():
    """Add a new address for the logged-in customer"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    data = request.get_json()
    result = addresses.add_customer_address(customer_id, data)

    status_code = 201 if result['success'] else 400
    return jsonify(result), status_code


@app.route('/api/addresses/<int:address_id>', methods=['PUT'])
def update_customer_address(address_id):
    """Update an existing address for the logged-in customer"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    data = request.get_json()
    result = addresses.update_customer_address(customer_id, address_id, data)

    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@app.route('/api/addresses/<int:address_id>', methods=['DELETE'])
def delete_customer_address(address_id):
    """Delete an address for the logged-in customer"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    result = addresses.delete_customer_address(customer_id, address_id)

    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@app.route('/api/addresses/<int:address_id>/default', methods=['PUT'])
def set_default_address(address_id):
    """Set an address as default for the logged-in customer"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    result = addresses.set_default_address(customer_id, address_id)

    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@app.route('/api/addresses/default', methods=['GET'])
def get_default_address():
    """Get the default address for the logged-in customer"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found'}), 401

    address = addresses.get_customer_default_address(customer_id)

    if address:
        return jsonify({'success': True, 'address': address})
    else:
        return jsonify({'success': True, 'address': None})


@app.route('/signout')
def signout():
    # Clear all session data
    session.clear()
    # Redirect to home page
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
