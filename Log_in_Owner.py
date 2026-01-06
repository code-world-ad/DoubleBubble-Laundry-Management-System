# Software Development project
# Log-in page for owner
# This module handles owner authentication from HTML form data

from flask import session

# Owner credentials (can be moved to database later)
OWNER_USERNAME = "admin"
OWNER_PASSWORD = "password123"


def authenticate_owner(username, password):
    """
    Authenticate an owner by checking username and password.
    
    Args:
        username (str): The owner's username
        password (str): The owner's password
    
    Returns:
        dict: Dictionary with 'success' (bool) and 'message' (str)
    """
    if username == OWNER_USERNAME and password == OWNER_PASSWORD:
        return {
            'success': True,
            'message': 'Owner login successful!'
        }
    else:
        # Check if username is correct but password is wrong
        if username == OWNER_USERNAME:
            return {
                'success': False,
                'message': 'Invalid password. Please check your credentials.'
            }
        else:
            return {
                'success': False,
                'message': 'Invalid username. Please check your credentials.'
            }


def owner_sign_in(request):
    """
    Handle owner sign-in request from HTML form.
    This function extracts username and password from Flask request object,
    validates credentials, and returns the authentication result.
    
    Args:
        request: Flask request object containing form data
    
    Returns:
        dict: Authentication result with 'success' (bool) and relevant data/message
    """
    # Get form data from HTML (field names match General Login.html)
    username = request.form.get('ownuser')  # HTML uses 'ownuser' as field name
    password = request.form.get('OwnPassword')  # HTML uses 'OwnPassword' as field name
    
    # Validate that required fields are provided
    if not username or not password:
        return {
            'success': False,
            'message': 'Username and password are required.'
        }
    
    # Authenticate the owner
    auth_result = authenticate_owner(username, password)
    
    # If successful, store owner data in session
    if auth_result['success']:
        session['owner_username'] = username
        session['owner_logged_in'] = True
    
    return auth_result
