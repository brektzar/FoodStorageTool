"""
Storage unit data model and operations
"""

import streamlit as st
from datetime import datetime
from utils.helpers import strip_emoji
from database import save_storage_data, load_storage_data

class StorageManager:
    def __init__(self):
        if 'storage_units' not in st.session_state:
            st.session_state.storage_units = load_storage_data()
    
    def add_unit(self, name, unit_type):
        """Add new storage unit"""
        if name not in st.session_state.storage_units:
            st.session_state.storage_units[name] = {
                "type": unit_type,
                "contents": {}
            }
            save_storage_data(st.session_state.storage_units)
            return True
        return False
    
    def add_item(self, unit_name, item_name, quantity, category, exp_date):
        """Add item to storage unit"""
        if unit_name in st.session_state.storage_units:
            st.session_state.storage_units[unit_name]['contents'][item_name] = {
                "quantity": quantity,
                "category": category,
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "expiration_date": exp_date.strftime("%Y-%m-%d")
            }
            save_storage_data(st.session_state.storage_units)
            return True
        return False
    
    def remove_item(self, unit_name, item_name, quantity=None):
        """Remove item or reduce quantity"""
        if unit_name in st.session_state.storage_units:
            unit = st.session_state.storage_units[unit_name]
            if item_name in unit['contents']:
                if quantity is None or quantity >= unit['contents'][item_name]['quantity']:
                    del unit['contents'][item_name]
                else:
                    unit['contents'][item_name]['quantity'] -= quantity
                save_storage_data(st.session_state.storage_units)
                return True
        return False 