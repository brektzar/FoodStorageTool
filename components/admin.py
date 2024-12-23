"""
Admin panel UI component
"""

import streamlit as st
import time
import yaml
from auth import add_user, delete_user, change_password, list_users, is_admin
from models.storage import StorageManager
from models.history import HistoryManager
from utils.constants import STORAGE_TYPES
from email_handler import (
    load_email_config, schedule_daily_notification, 
    get_email_schedule_info, format_weekdays,
    send_expiration_notification
)

def render_admin_view():
    """Render the admin panel view"""
    if not is_admin():
        st.error("Endast administratörer har tillgång till denna sida")
        return

    st.title("⚙️ Administratörsinställningar")
    st.warning("🚨Varning🚨: Dessa funktioner kan skapa instabilitet och påverka all lagrad data!")

    # Create tabs for different admin sections
    tabs = st.tabs([
        "⚙️ Datahantering",
        "👥 Användarhantering",
        "📧 Email-notifieringar"
    ])

    with tabs[0]:
        render_data_management()
    with tabs[1]:
        render_user_management()
    with tabs[2]:
        render_email_settings()

def render_data_management():
    """Render data management section"""
    storage_mgr = StorageManager()
    history_mgr = HistoryManager()

    with st.expander("⚙️ Inställningar för data"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Hantera exempeldata")
            if st.button("Lägg till exempel-data", type="secondary"):
                populate_example_data(storage_mgr, history_mgr)

            if st.button("Rensa endast exempeldata", type="secondary"):
                clear_example_data(storage_mgr, history_mgr)

        with col2:
            st.subheader("Rensa specifik data")
            if st.button("Rensa förvaringsenheter", type="secondary"):
                st.session_state.storage_units = {}
                storage_mgr.save()
                st.success("Alla förvaringsenheter har rensats!")

            if st.button("Rensa historik", type="secondary"):
                st.session_state.item_history = []
                history_mgr.save()
                st.success("All historik har rensats!")

        # Clear all data section
        st.subheader("Rensa all data")
        clear_all = st.button("Rensa ALL data", type="secondary")
        confirm = st.checkbox("Jag förstår att detta kommer radera ALL data permanent")

        if clear_all:
            if confirm:
                clear_all_data(storage_mgr, history_mgr)
                st.success("All data har rensats!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Du måste bekräfta att du vill radera all data")

def render_user_management():
    """Render user management section"""
    with st.expander("👥 Användarhantering"):
        # Show existing users
        users = list_users()
        if users:
            st.write("### Befintliga användare")
            for username, data in users.items():
                st.write(f"- {username} ({data['role']})")

        # Add new user
        st.subheader("Lägg till ny användare")
        new_username = st.text_input("Användarnamn")
        new_password = st.text_input("Lösenord", type="password")
        new_role = st.selectbox("Roll", options=['user', 'admin'])

        if st.button("Skapa användare"):
            if new_username and new_password:
                success, message = add_user(new_username, new_password, new_role)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("Både användarnamn och lösenord krävs")

        # Change password section
        st.subheader("Ändra lösenord")
        user_to_change = st.selectbox(
            "Välj användare",
            options=list(users.keys())
        )
        new_password = st.text_input("Nytt lösenord", type="password", key="change_pwd")
        confirm_password = st.text_input("Bekräfta nytt lösenord", type="password")

        if st.button("Ändra lösenord"):
            if new_password and confirm_password:
                if new_password == confirm_password:
                    success, message = change_password(user_to_change, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Lösenorden matchar inte")
            else:
                st.error("Både lösenord och bekräftelse krävs")

        # Delete user section
        st.subheader("Ta bort användare")
        user_to_delete = st.selectbox(
            "Välj användare att ta bort",
            options=[u for u in users.keys() if u != 'admin']
        )
        confirm_delete = st.checkbox("Jag är säker på att jag vill ta bort denna användare")

        if st.button("Ta bort användare"):
            if confirm_delete:
                success, message = delete_user(user_to_delete)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Bekräfta borttagning genom att markera checkboxen")

def render_email_settings():
    """Render email notification settings"""
    with st.expander("📧 Email-notifieringar"):
        config = load_email_config()
        if config and config['email']['notifications'].get('recipient'):
            render_current_email_status(config)
            render_email_schedule_settings(config)
            render_notification_preferences(config)
        else:
            render_email_setup()

def render_current_email_status(config):
    """Render current email notification status"""
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"Email-notifieringar är aktiva för: {config['email']['notifications']['recipient']}")
        last_sent, next_send = get_email_schedule_info()
        if last_sent:
            st.info(f"Senaste email skickades {format_last_sent(last_sent)}")
        if next_send:
            st.info(f"Nästa email skickas {format_next_send(next_send)}")

    with col2:
        if st.button("Skicka test-email"):
            send_test_notification(config)

def populate_example_data(storage_mgr, history_mgr):
    """Add example data to the system"""
    # Implementation of example data population
    pass

def clear_example_data(storage_mgr, history_mgr):
    """Clear only example data"""
    # Implementation of example data clearing
    pass

def clear_all_data(storage_mgr, history_mgr):
    """Clear all data from the system"""
    # Implementation of complete data clearing
    pass 