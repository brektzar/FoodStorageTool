"""
Autentiseringshantering för Matförvaringsappen
"""

import streamlit as st
import hashlib

def load_users():
    """Load user configuration from secrets"""
    try:
        users = {}
        user_data = st.secrets.get("users", {})
        user_roles = st.secrets.get("user_roles", {})
        
        for username in user_data:
            users[username] = {
                'password': user_data[username],
                'role': user_roles.get(username, 'user')  # Default to 'user' if role not specified
            }
        return users
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

# Hascha lösenord för säker jämförelse
def hash_password(password):
    """Hasha lösenord för säker jämförelse"""
    # Add salt and use consistent encoding
    salt = "matforvaring_salt"  # Adding a constant salt
    salted = (password + salt).encode('utf-8')
    return hashlib.sha256(salted).hexdigest()

# Add this temporarily after the hash_password function
def debug_password_hash(password):
    hashed = hash_password(password)
    print(f"Hash for '{password}': {hashed}")
    return hashed

# Kontrollera om användaren är admin
def is_admin():
    if 'user_role' in st.session_state:
        return st.session_state.user_role == 'admin'
    return False

# Kontrollera om användaren är inloggad
def is_logged_in():
    return 'logged_in' in st.session_state and st.session_state.logged_in

# Hantera inloggning
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
                    
                    # Debug prints
                    print("=== Debug Info ===")
                    print(f"Username: {username}")
                    print(f"Input password: {password}")
                    print(f"Input hash: {input_hash}")
                    print(f"Stored hash: {stored_hash}")
                    print("=================")
                    
                    if input_hash == stored_hash:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = users[username]['role']
                        st.rerun()
                    else:
                        st.error("Felaktigt lösenord")
                else:
                    st.error("Användaren finns inte eller är inte korrekt konfigurerad")
            except Exception as e:
                st.error(f"Inloggningsfel: {str(e)}")
            return False
    return st.session_state.logged_in

# Logga ut användaren
def logout():
    if st.sidebar.button("Logga ut"):
        for key in ['logged_in', 'username', 'user_role']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun() 

def add_user(username, password, role='user'):
    """Lägg till ny användare"""
    try:
        # Verify user doesn't exist
        users = load_users()
        if username in users:
            return False, "Användarnamnet finns redan"
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Prepare data for saving
        users_data = {name: data['password'] for name, data in users.items()}
        roles_data = {name: data['role'] for name, data in users.items()}
        
        # Add new user
        users_data[username] = hashed_password
        roles_data[username] = role
        
        # Save to file
        success, message = save_users(users_data, roles_data)
        if success:
            st.rerun()
            return True, f"Användare {username} skapades"
        if "Kopiera följande innehåll" in message:
            st.code(message.split("```toml\n")[1].split("```")[0], language="toml")
            st.info("Kopiera innehållet ovan till Streamlit Cloud secrets och försök igen.")
        return False, message
        
    except Exception as e:
        return False, f"Fel vid skapande av användare: {str(e)}"

def delete_user(username):
    """Ta bort användare"""
    try:
        users = load_users()
        if username not in users:
            return False, "Användaren finns inte"
        
        if username == 'admin':
            return False, "Kan inte ta bort huvudadmin"
        
        # Prepare data for saving
        users_data = {name: data['password'] for name, data in users.items() if name != username}
        roles_data = {name: data['role'] for name, data in users.items() if name != username}
        
        # Save to file
        success, message = save_users(users_data, roles_data)
        if success:
            st.rerun()
            return True, f"Användare {username} togs bort"
        return False, message
        
    except Exception as e:
        return False, f"Fel vid borttagning av användare: {str(e)}"

def list_users():
    """Hämta lista över alla användare
    
    Returns:
        dict: Användardata (utan lösenord)
    """
    try:
        users = load_users()
        # Return user data without passwords
        return {username: {'role': data['role']} for username, data in users.items()}
    except Exception:
        return {}

def change_password(username, new_password):
    """Change user password"""
    try:
        users = load_users()
        if username not in users:
            return False, "Användaren finns inte"

        # Hash the new password
        hashed_password = hash_password(new_password)
        
        # Prepare data for saving
        users_data = {name: data['password'] for name, data in users.items()}
        roles_data = {name: data['role'] for name, data in users.items()}
        
        # Update password
        users_data[username] = hashed_password
        
        # Save to file
        success, message = save_users(users_data, roles_data)
        if success:
            return True, f"Lösenord ändrat för {username}"
        return False, message
        
    except Exception as e:
        return False, f"Fel vid ändring av lösenord: {str(e)}"

def save_users(users_data, roles_data):
    """Save users and roles to secrets.toml
    
    Args:
        users_data (dict): Dictionary of usernames and hashed passwords
        roles_data (dict): Dictionary of usernames and roles
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        secrets_path = '.streamlit/secrets.toml'
        
        # Generate the new secrets content
        new_secrets = []
        
        # Add users section
        new_secrets.append('[users]\n')
        for username, password in users_data.items():
            new_secrets.append(f'{username} = "{password}"\n')
        
        # Add roles section
        new_secrets.append('\n[user_roles]\n')
        for username, role in roles_data.items():
            new_secrets.append(f'{username} = "{role}"\n')
        
        # Try to write to file
        try:
            with open(secrets_path, 'w') as f:
                f.writelines(new_secrets)
            return True, "Users saved successfully"
        except (PermissionError, FileNotFoundError):
            # If we can't write to the file, return the content that needs to be copied
            secrets_content = ''.join(new_secrets)
            error_message = (
                "Kunde inte spara till secrets.toml. "
                "Kopiera följande innehåll till Streamlit Cloud secrets:\n\n"
                f"```toml\n{secrets_content}```"
            )
            return False, error_message
            
    except Exception as e:
        return False, f"Error saving users: {str(e)}"