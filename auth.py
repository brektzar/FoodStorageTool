"""
Authentication handling for the Food Storage App
"""

import streamlit as st
import hashlib
from email_handler import send_user_management_notification

def hash_password(password):
    """Hash password for secure comparison"""
    return hashlib.sha256(password.encode()).hexdigest()

def is_admin():
    """Check if current user is admin"""
    if 'user_role' in st.session_state:
        return st.session_state.user_role == 'admin'
    return False

def is_logged_in():
    """Check if user is logged in"""
    return 'logged_in' in st.session_state and st.session_state.logged_in

def login():
    """Handle user login"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.header("🔐 Logga in")
        username = st.text_input("Användarnamn")
        password = st.text_input("Lösenord", type="password")
        
        if st.button("Logga in"):
            try:
                # Get user data from secrets
                users = st.secrets.users
                if username in users:
                    stored_data = users[username]
                    input_hash = hash_password(password)
                    
                    if input_hash == stored_data['password']:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = stored_data['role']
                        st.rerun()
                    else:
                        st.error("Felaktigt lösenord")
                else:
                    st.error("Användaren finns inte")
            except Exception as e:
                st.error(f"Inloggningsfel: {str(e)}")
            return False
    return st.session_state.logged_in

def logout():
    """Log out user"""
    if st.sidebar.button("Logga ut"):
        for key in ['logged_in', 'username', 'user_role']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

def add_user(username, password, role='user'):
    """Add a new user and show admin the credentials for secrets.toml"""
    hashed_password = hash_password(password)
    
    # Show admin what to add to secrets
    st.info("Please add the following to your Streamlit Cloud secrets:")
    st.code(f"""[users.{username}]
password = "{hashed_password}"
role = "{role}"
""", language='toml')
    
    # Send notification about new user
    send_user_management_notification(
        "created", 
        username, 
        performed_by=st.session_state.get('username', 'Unknown')
    )
    return True, f"User {username} created successfully"

def check_password(username, password):
    """Check if username/password combo is valid"""
    try:
        stored_data = st.secrets.users[username]
        if stored_data['password'] == hash_password(password):
            return True
    except (KeyError, AttributeError):
        pass
    return False

def delete_user(username):
    """Delete user"""
    try:
        if username == 'admin':
            return False, "Cannot delete main admin"
            
        st.info("Please remove the following section from your Streamlit Cloud secrets:")
        st.code(f"""[users.{username}]""", language='toml')

        # Send notification about deleted user
        send_user_management_notification(
            "deleted", 
            username, 
            performed_by=st.session_state.get('username', 'Unknown')
        )
        return True, f"User {username} marked for deletion"
    except Exception as e:
        return False, f"Error deleting user: {str(e)}"

def list_users():
    """Get list of all users and their roles"""
    try:
        users = st.secrets.users
        return {username: {'role': data['role']} for username, data in users.items()}
    except Exception:
        return {}