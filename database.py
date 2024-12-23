"""
Database handler for persistent storage using MongoDB
"""

import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import json
import os
import dns.resolver

# Initialize connection
@st.cache_resource
def init_connection():
    """Initialize MongoDB connection using st.cache_resource to only run once"""
    try:
        # Configure DNS resolver to use Google's DNS
        dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
        dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']

        # Create a new client and connect to the server with ServerApi
        client = MongoClient(
            st.secrets["mongo"]["uri"],
            server_api=ServerApi('1'),
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            serverSelectionTimeoutMS=30000,
            directConnection=False,
            connect=True
        )
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        st.success("Successfully connected to MongoDB!")
        return client
    except Exception as e:
        st.error(f"Could not connect to database: {str(e)}")
        return None

def get_database():
    """Get MongoDB database connection"""
    if 'mongodb' not in st.session_state:
        client = init_connection()
        if client is not None:
            st.session_state.mongodb = client.matforvaring
        else:
            st.warning("Falling back to local storage...")
            return None
    return st.session_state.mongodb

# Pull data with caching
@st.cache_data(ttl=600)  # Match the documentation's TTL
def load_storage_data():
    """Load storage units data from MongoDB or locally"""
    # Clear the cache if clear_cache flag is set
    if st.session_state.get('clear_cache', False):
        load_storage_data.clear()
        st.session_state.clear_cache = False
    
    db = get_database()
    if db is not None:
        try:
            # Make the result hashable for st.cache_data as shown in docs
            data = list(db.storage_units.find())  # Convert cursor to list
            if data:
                # Remove MongoDB's _id field from all documents
                for doc in data:
                    doc.pop('_id', None)
                # Return the actual storage units data, not the whole document
                return data[0] if isinstance(data[0], dict) else {}
            return {}
        except Exception as e:
            st.error(f"Error loading from database: {str(e)}")
            return load_local_storage_data()
    else:
        return load_local_storage_data()

def save_storage_data(data):
    """Save storage units data to MongoDB or locally"""
    db = get_database()
    if db is not None:
        try:
            # Ensure we're saving a dictionary
            if not isinstance(data, dict):
                st.error("Invalid data format")
                return False
                
            json_data = json.loads(json.dumps(data, default=str))
            # Clear existing data and insert new
            db.storage_units.delete_many({})
            db.storage_units.insert_one(json_data)
            
            # Set flag to clear cache on next load
            st.session_state.clear_cache = True
            return True
        except Exception as e:
            st.error(f"Error saving storage data: {str(e)}")
            try:
                with open('storage_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            except Exception as e:
                st.error(f"Error saving to local storage: {str(e)}")
    else:
        try:
            with open('storage_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error saving to local storage: {str(e)}")
    return False

def save_history_data(data):
    """Save history data to MongoDB"""
    db = get_database()
    if db is not None:
        try:
            json_data = json.loads(json.dumps(data, default=str))
            db.history.replace_one({}, {"history": json_data}, upsert=True)
            return True
        except Exception as e:
            st.error(f"Error saving history data: {str(e)}")
            # Fallback to local storage
            try:
                with open('history_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            except Exception as e:
                st.error(f"Error saving to local storage: {str(e)}")
    else:
        try:
            with open('history_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error saving to local storage: {str(e)}")
    return False

def load_history_data():
    """Load history data from MongoDB"""
    db = get_database()
    if db is not None:
        try:
            data = db.history.find_one()
            if data is not None:
                return data.get("history", [])
            return []
        except Exception as e:
            st.error(f"Error loading history data: {str(e)}")
            return load_local_history_data()
    else:
        return load_local_history_data()

def load_local_history_data():
    """Load history data from local file"""
    try:
        if os.path.exists('history_data.json'):
            with open('history_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading from local storage: {str(e)}")
        return []

def save_reminders_data(data):
    """Save reminders data to MongoDB"""
    db = get_database()
    if db is not None:
        try:
            json_data = json.loads(json.dumps(data, default=str))
            db.reminders.replace_one({}, json_data, upsert=True)
            return True
        except Exception as e:
            st.error(f"Error saving reminders data: {str(e)}")
            try:
                with open('reminders_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            except Exception as e:
                st.error(f"Error saving to local storage: {str(e)}")
    else:
        try:
            with open('reminders_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error saving to local storage: {str(e)}")
    return False

def load_reminders_data():
    """Load reminders data from MongoDB"""
    db = get_database()
    if db is not None:
        try:
            data = db.reminders.find_one()
            if data is not None:
                data.pop('_id', None)
                return data
            return {}
        except Exception as e:
            st.error(f"Error loading reminders data: {str(e)}")
            return load_local_reminders_data()
    else:
        return load_local_reminders_data()

def load_local_reminders_data():
    """Load reminders data from local file"""
    try:
        if os.path.exists('reminders_data.json'):
            with open('reminders_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.error(f"Error loading from local storage: {str(e)}")
        return {}

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