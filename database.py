"""
Database handler for persistent storage using MongoDB
"""

import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import json
import os
import time

def get_database():
    """Get MongoDB database connection"""
    if 'mongodb' not in st.session_state:
        # Number of connection attempts
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Get MongoDB connection string from secrets
                mongo_uri = st.secrets["mongodb"]["connection_string"]
                
                # Add DNS settings and other options
                client = MongoClient(
                    mongo_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000,
                    direct=True,
                    dns_resolver='8.8.8.8',  # Use Google's DNS
                    retryWrites=True,
                    w='majority'
                )
                
                # Test the connection
                client.server_info()
                st.session_state.mongodb = client.matforvaring
                return st.session_state.mongodb
                
            except Exception as e:
                if attempt < max_retries - 1:
                    st.warning(f"Connection attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    st.error(f"Could not connect to database after {max_retries} attempts: {str(e)}")
                    st.warning("Falling back to local storage...")
                    return None
    
    return st.session_state.mongodb

def save_storage_data(data):
    """Save storage units data to MongoDB or locally"""
    db = get_database()
    if db:
        try:
            json_data = json.loads(json.dumps(data, default=str))
            db.storage_units.replace_one({}, json_data, upsert=True)
            return True
        except Exception as e:
            st.error(f"Error saving storage data: {str(e)}")
            # Fallback to local storage
            try:
                with open('storage_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            except Exception as e:
                st.error(f"Error saving to local storage: {str(e)}")
    else:
        # Save locally if no database connection
        try:
            with open('storage_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error saving to local storage: {str(e)}")
    return False

def load_storage_data():
    """Load storage units data from MongoDB or locally"""
    db = get_database()
    if db:
        try:
            data = db.storage_units.find_one()
            if data:
                data.pop('_id', None)
                return data
            return {}
        except Exception as e:
            st.error(f"Error loading from database: {str(e)}")
            # Fallback to local storage
            return load_local_storage_data()
    else:
        # Load from local storage if no database connection
        return load_local_storage_data()

def load_local_storage_data():
    """Load data from local JSON file"""
    try:
        if os.path.exists('storage_data.json'):
            with open('storage_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.error(f"Error loading from local storage: {str(e)}")
        return {}

def save_history_data(data):
    """Save history data to MongoDB"""
    db = get_database()
    if db:
        try:
            json_data = json.loads(json.dumps(data, default=str))
            db.history.replace_one({}, {"history": json_data}, upsert=True)
            return True
        except Exception as e:
            st.error(f"Error saving history data: {str(e)}")
    return False

def load_history_data():
    """Load history data from MongoDB"""
    db = get_database()
    if db:
        try:
            data = db.history.find_one()
            if data:
                return data.get("history", [])
            return []
        except Exception as e:
            st.error(f"Error loading history data: {str(e)}")
    return []

def save_reminders_data(data):
    """Save reminders data to MongoDB"""
    db = get_database()
    if db:
        try:
            json_data = json.loads(json.dumps(data, default=str))
            db.reminders.replace_one({}, json_data, upsert=True)
            return True
        except Exception as e:
            st.error(f"Error saving reminders data: {str(e)}")
    return False

def load_reminders_data():
    """Load reminders data from MongoDB"""
    db = get_database()
    if db:
        try:
            data = db.reminders.find_one()
            if data:
                data.pop('_id', None)
                return data
            return {}
        except Exception as e:
            st.error(f"Error loading reminders data: {str(e)}")
    return {} 