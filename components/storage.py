"""
Storage management UI component
"""

import streamlit as st
from datetime import datetime, timedelta
from utils.constants import STORAGE_TYPES, FOOD_CATEGORIES
from models.storage import StorageManager
from models.history import HistoryManager

def render_storage_view():
    """Render the storage management view"""
    st.title("📦 Förvarade Varor")
    
    storage_mgr = StorageManager()
    history_mgr = HistoryManager()

    # Check if there are any storage units
    if not st.session_state.storage_units:
        st.warning("Inga förvaringsenheter finns tillgängliga. Be en administratör att lägga till förvaringsenheter.")
        return

    # Storage unit selector
    selected_unit = st.selectbox(
        "Välj förvaringsenhet",
        options=list(st.session_state.storage_units.keys()),
        key="unit_selector_1"
    )

    if selected_unit:
        unit = st.session_state.storage_units[selected_unit]
        render_unit_contents(selected_unit, unit, storage_mgr, history_mgr)

def render_unit_contents(unit_name, unit, storage_mgr, history_mgr):
    """Render contents and controls for a storage unit"""
    # Add item section
    with st.expander("Lägg till ny vara"):
        render_add_item_form(unit_name, unit, storage_mgr, history_mgr)

    # Show contents
    if unit['contents']:
        st.write("### 📦 Innehåll")
        render_unit_items(unit_name, unit, storage_mgr, history_mgr)
    else:
        st.info("📭 Inga varor tillagda än!")

def render_add_item_form(unit_name, unit, storage_mgr, history_mgr):
    """Render form for adding new items"""
    st.subheader(f"{unit_name} ({unit['type']})")
    
    input_method = st.radio(
        "Välj inmatningsmetod",
        ["Välj från tidigare varor", "Skriv in ny vara"],
        horizontal=True
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if input_method == "Skriv in ny vara":
            new_item = st.text_input("Lägg till vara")
        else:
            new_item = render_previous_items_selector()
            
    with col2:
        quantity = st.number_input("Antal", min_value=1, value=1)
    with col3:
        category = st.selectbox("Kategori", FOOD_CATEGORIES)

    exp_date = st.date_input(
        "Utgångsdatum",
        min_value=datetime.now().date(),
        value=datetime.now().date() + timedelta(days=7)
    )

    if st.button("Lägg till vara"):
        if new_item:
            if storage_mgr.add_item(unit_name, new_item, quantity, category, exp_date):
                history_mgr.add_entry('added', new_item, category, quantity, unit_name, exp_date=exp_date.strftime("%Y-%m-%d"))
                st.success(f"Lade till {quantity} {new_item}") 

def render_previous_items_selector():
    """Render selector for previously used items"""
    # Get unique items from history
    previous_items = set()
    for history_item in st.session_state.item_history:
        previous_items.add(history_item['item'])
    # Add current items from all storage units
    for storage_unit in st.session_state.storage_units.values():
        for item in storage_unit['contents'].keys():
            previous_items.add(item)

    if previous_items:
        return st.selectbox(
            "Välj vara",
            options=sorted(list(previous_items))
        )
    else:
        st.info("Inga tidigare varor att välja från.")
        return st.text_input("Lägg till vara")

def render_unit_items(unit_name, unit, storage_mgr, history_mgr):
    """Render list of items in storage unit"""
    for item, details in unit['contents'].items():
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            st.write(f"{item} ({details['category']})")
        with col2:
            st.write(f"📊 Antal: {details['quantity']}")
        with col3:
            st.write(f"📅 Tillagd: {details['date_added']}")
        with col4:
            st.write(f"⏳ Utgår: {details['expiration_date']}")
        with col5:
            remove_key = f"remove_{item}"
            if st.button("🗑️ Ta bort", key=remove_key):
                st.session_state[f"show_quantity_selector_{item}"] = True

        # Quantity selector for removal
        if st.session_state.get(f"show_quantity_selector_{item}", False):
            with st.expander(f"Hur många {item} vill du ta bort?", expanded=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    remove_quantity = st.number_input(
                        "Antal att ta bort",
                        min_value=1,
                        max_value=details['quantity'],
                        value=1,
                        key=f"remove_quantity_{item}"
                    )
                with col2:
                    if st.button("Bekräfta", key=f"confirm_remove_{item}"):
                        expired = datetime.strptime(details['expiration_date'], "%Y-%m-%d").date() < datetime.now().date()
                        if storage_mgr.remove_item(unit_name, item, remove_quantity):
                            history_mgr.add_entry(
                                'removed',
                                item,
                                details['category'],
                                remove_quantity,
                                unit_name,
                                expired=expired,
                                exp_date=details['expiration_date']
                            )
                            del st.session_state[f"show_quantity_selector_{item}"]
                            st.rerun()
                            
                    if st.button("Avbryt", key=f"cancel_remove_{item}"):
                        del st.session_state[f"show_quantity_selector_{item}"]
                        st.rerun()