"""
History data model and operations
"""

import streamlit as st
from datetime import datetime
from utils.helpers import strip_emoji
from databasepy import save_history_data, load_history_data

class HistoryManager:
    def __init__(self):
        if 'item_history' not in st.session_state:
            st.session_state.item_history = load_history_data()

    def add_entry(self, action, item_name, category, quantity, storage_unit, 
                 expired=False, exp_date=None, is_example=False):
        """Add new history entry
        
        Args:
            action (str): Type of action ('added' or 'removed')
            item_name (str): Name of the item
            category (str): Item category
            quantity (int): Item quantity
            storage_unit (str): Storage unit name
            expired (bool): Whether item was expired
            exp_date (str): Expiration date (YYYY-MM-DD)
            is_example (bool): Whether this is example data
        """
        history_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'action': action,
            'item': item_name,
            'category': strip_emoji(category),
            'quantity': quantity,
            'storage_unit': storage_unit,
            'expired': expired,
            'expiration_date': exp_date,
            'is_example': is_example,
            'username': st.session_state.get('username', 'Okänd')
        }
        
        st.session_state.item_history.append(history_entry)
        save_history_data(st.session_state.item_history)
        return history_entry

    def get_filtered_history(self, days=None, category=None, action=None):
        """Get filtered history entries
        
        Args:
            days (int): Number of days to look back
            category (str): Filter by category
            action (str): Filter by action type
        
        Returns:
            list: Filtered history entries
        """
        history = st.session_state.item_history
        
        if days is not None:
            cutoff = datetime.now() - timedelta(days=days)
            history = [
                entry for entry in history 
                if datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S") > cutoff
            ]
        
        if category:
            history = [
                entry for entry in history 
                if entry['category'] == strip_emoji(category)
            ]
            
        if action:
            history = [
                entry for entry in history 
                if entry['action'] == action
            ]
            
        return history

    def clear_example_data(self):
        """Remove all example data from history"""
        st.session_state.item_history = [
            entry for entry in st.session_state.item_history 
            if not entry.get('is_example', False)
        ]
        save_history_data(st.session_state.item_history) 