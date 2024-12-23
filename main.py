"""
MATFÖRVARINGSHANTERARE
======================

En applikation för att hålla koll på innehållet i kylskåp, frysar och andra matförvaringsenheter.
"""

import streamlit as st
from auth import login, logout, is_admin, is_logged_in
from components.storage import render_storage_view
from components.statistics import render_statistics_view
from components.admin import render_admin_view
from databasepy import init_connection

# Initialize MongoDB connection
if 'mongodb_initialized' not in st.session_state:
    init_connection()
    st.session_state.mongodb_initialized = True

# Single authentication check that includes the logout button
if not is_logged_in():
    login()
    st.stop()
else:
    # Add logout button in sidebar
    with st.sidebar:
        if st.button("Logga ut"):
            logout()
            st.rerun()

# Create tabs based on user role
tabs = ["📦 Förvaring", "📊 Statistik"]
if is_admin():
    tabs.append("⚙️ Admin")

# Create and render tabs
selected_tab = st.tabs(tabs)

# Render appropriate view based on selected tab
with selected_tab[0]:
    render_storage_view()

with selected_tab[1]:
    render_statistics_view()

if is_admin() and len(selected_tab) > 2:
    with selected_tab[2]:
        render_admin_view()
