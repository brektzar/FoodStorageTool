"""
Storage unit data model and operations
"""

import streamlit as st
from datetime import datetime
from utils.helpers import strip_emoji
from databasepy import save_storage_data, load_storage_data

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
    
    def get_expiring_items(self):
        """Get list of items that are expired or about to expire
        
        Returns:
            list: List of dictionaries containing item details
        """
        expiring_items = []
        current_date = datetime.now().date()
        
        for unit_name, unit in st.session_state.storage_units.items():
            for item_name, details in unit['contents'].items():
                exp_date = datetime.strptime(details['expiration_date'], "%Y-%m-%d").date()
                days_remaining = (exp_date - current_date).days
                
                if days_remaining <= 7:  # Include items expiring within a week
                    expiring_items.append({
                        'item': item_name,
                        'unit': unit_name,
                        'days': days_remaining,
                        'exp_date': details['expiration_date'],
                        'category': details['category'],
                        'quantity': details['quantity']
                    })
        
        return expiring_items