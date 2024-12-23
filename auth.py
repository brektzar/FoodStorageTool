"""
Autentiseringshantering för Matförvaringsappen
"""

import streamlit as st
import yaml
from yaml.loader import SafeLoader
import hashlib

# Ladda användarkonfiguration från YAML-fil
def load_users():
    """Load user configuration from YAML file and secrets"""
    with open('users.yml') as file:
        users = yaml.load(file, Loader=SafeLoader)
        # Track users to remove
        users_to_remove = []
        
        # Add passwords from secrets directly (without hashing)
        for username, user_data in users.items():
            try:
                user_data['password'] = st.secrets["users"][username]
            except KeyError:
                users_to_remove.append(username)
        
        # Remove users without passwords
        for username in users_to_remove:
            del users[username]
            
        return users

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

def save_users(users):
    """Spara användardata till YAML-fil"""
    # Create a new dict with only roles
    users_to_save = {
        username: {'role': user_data['role']} 
        for username, user_data in users.items()
    }
    with open('users.yml', 'w') as file:
        yaml.dump(users_to_save, file)

def add_user(username, password, role='user'):
    """Lägg till ny användare"""
    try:
        # Update users.yml
        users = load_users()
        if username in users:
            return False, "Användarnamnet finns redan"
        
        users[username] = {
            'role': role
        }
        save_users(users)

        # Hash the password before storing
        hashed_password = hash_password(password)

        # Update secrets.toml
        secrets_path = '.streamlit/secrets.toml'
        with open(secrets_path, 'r') as f:
            secrets_content = f.readlines()
        
        # Find [users] section and add new user
        new_secrets = []
        in_users_section = False
        for line in secrets_content:
            if '[users]' in line:
                in_users_section = True
            new_secrets.append(line)
            if in_users_section and line.strip() == '[users]':
                new_secrets.append(f'{username} = "{hashed_password}"\n')
        
        if not in_users_section:
            new_secrets.extend(['\n[users]\n', f'{username} = "{hashed_password}"\n'])

        with open(secrets_path, 'w') as f:
            f.writelines(new_secrets)

        return True, f"Användare {username} skapades"
    except Exception as e:
        return False, f"Fel vid skapande av användare: {str(e)}"

def delete_user(username):
    """Ta bort användare"""
    try:
        # Update users.yml
        users = load_users()
        if username not in users:
            return False, "Användaren finns inte"
        
        if username == 'admin':
            return False, "Kan inte ta bort huvudadmin"
            
        del users[username]
        save_users(users)

        # Update secrets.toml
        secrets_path = '.streamlit/secrets.toml'
        with open(secrets_path, 'r') as f:
            secrets_content = f.readlines()
        
        # Remove user from secrets
        new_secrets = []
        skip_line = False
        for line in secrets_content:
            if f'{username} = "' in line:
                skip_line = True
                continue
            new_secrets.append(line)
        
        with open(secrets_path, 'w') as f:
            f.writelines(new_secrets)

        return True, f"Användare {username} togs bort"
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
        # Verify user exists
        users = load_users()
        if username not in users:
            return False, "Användaren finns inte"

        # Hash the new password
        hashed_password = hash_password(new_password)

        # Update secrets.toml
        secrets_path = '.streamlit/secrets.toml'
        with open(secrets_path, 'r') as f:
            secrets_content = f.readlines()
        
        # Replace password in secrets
        new_secrets = []
        password_updated = False
        for line in secrets_content:
            if f'{username} = "' in line:
                new_secrets.append(f'{username} = "{hashed_password}"\n')
                password_updated = True
            else:
                new_secrets.append(line)
        
        if not password_updated:
            return False, "Kunde inte hitta användaren i secrets"

        with open(secrets_path, 'w') as f:
            f.writelines(new_secrets)

        return True, f"Lösenord ändrat för {username}"
    except Exception as e:
        return False, f"Fel vid ändring av lösenord: {str(e)}"