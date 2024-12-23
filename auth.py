"""
Authentication handling for Matförvaringsappen
"""

import streamlit as st
import hashlib

def hash_password(password):
    """Hash password for secure comparison"""
    salt = "matforvaring_salt"  # Adding a constant salt
    salted = (password + salt).encode('utf-8')
    return hashlib.sha256(salted).hexdigest()

def load_users():
    """Load user configuration from secrets"""
    try:
        users = {}
        # Get all users from secrets
        for username, user_data in st.secrets.get("users", {}).items():
            if isinstance(user_data, dict):
                # New format where user_data is a dict with 'password' and 'role'
                users[username] = user_data
            else:
                # Old format where user_data is just the password
                users[username] = {
                    'password': user_data,
                    'role': 'admin' if username == 'admin' else 'user'
                }
        return users
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")
        return {}

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
                users = load_users()
                if username in users:
                    input_hash = hash_password(password)
                    stored_hash = users[username]['password']
                    
                    if input_hash == stored_hash:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = users[username]['role']
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
    """Add new user to secrets.toml
    
    Note: This function provides instructions for manual update
    since Streamlit secrets are read-only at runtime.
    """
    try:
        users = load_users()
        if username in users:
            return False, "Användarnamnet finns redan"
        
        hashed_password = hash_password(password)
        
        # Provide instructions for updating secrets.toml
        instructions = f"""
To add the new user, add these lines to .streamlit/secrets.toml:

[users.{username}]
password = "{hashed_password}"
role = "{role}"
"""
        return True, instructions

    except Exception as e:
        return False, f"Fel vid skapande av användare: {str(e)}"

def delete_user(username):
    """Provide instructions for deleting a user from secrets.toml"""
    try:
        users = load_users()
        if username not in users:
            return False, "Användaren finns inte"
        
        if username == 'admin':
            return False, "Kan inte ta bort huvudadmin"
            
        # Provide instructions for updating secrets.toml
        instructions = f"""
To remove the user, delete these lines from .streamlit/secrets.toml:

[users.{username}]
password = "..."
role = "..."
"""
        return True, instructions

    except Exception as e:
        return False, f"Fel vid borttagning av användare: {str(e)}"

def list_users():
    """Get list of all users (without passwords)
    
    Returns:
        dict: User data (without passwords)
    """
    try:
        users = load_users()
        # Return user data without passwords
        return {username: {'role': data['role']} for username, data in users.items()}
    except Exception:
        return {}

def change_password(username, new_password):
    """Provide instructions for changing a user's password in secrets.toml"""
    try:
        users = load_users()
        if username not in users:
            return False, "Användaren finns inte"

        hashed_password = hash_password(new_password)
        
        # Provide instructions for updating secrets.toml
        instructions = f"""
To change the password, update this line in .streamlit/secrets.toml:

[users.{username}]
password = "{hashed_password}"
role = "{users[username]['role']}"
"""
        return True, instructions

    except Exception as e:
        return False, f"Fel vid ändring av lösenord: {str(e)}"