"""
MATFÖRVARINGSHANTERARE
======================

En applikation för att hålla koll på innehållet i kylskåp, frysar och andra matförvaringsenheter.

Huvudfunktioner:
---------------
1. Förvaringshantering
   - Skapa och hantera olika förvaringsenheter (kylskåp, frys, skafferi, etc.)
   - Lägg till och ta bort varor i varje enhet
   - Spåra mängd, kategori och datum för varje vara

2. Utgångsdatumhantering
   - Automatisk varning för varor som närmar sig utgångsdatum
   - Tydlig markering av utgångna varor
   - Påminnelsesystem med anpassningsbara tidsintervall
   - Spårning av utgångsmönster

3. Statistik och Analys
   - Detaljerad statistik över användningsmönster
   - Visualisering av data genom grafer och diagram
   - Filtrering av data baserat på tidsperioder
   - Analys av utgångsmönster och matsvinn

4. Datahantering
   - Persistent lagring av all data i JSON-format
   - Möjlighet att lägga till exempeldata
   - Separata kontroller för olika datatyper
   - Säkerhetskopieringsmöjligheter

Tekniska funktioner:
------------------
- Automatisk datumhantering och validering
- Responsiv design som fungerar på både desktop och mobil
- Cachad statistikgenerering för bättre prestanda
- Felhantering för korrupta eller saknade datafiler
- Stöd för svenska tecken och emojis

Användargränssnitt:
-----------------
- Sidofält för snabb åtkomst till viktiga funktioner
- Flikbaserad navigation mellan förvaring och statistik
- Expanderbara sektioner för bättre översikt
- Tydliga varningar och bekräftelsedialoger
- Administratörskontroller för datahantering

Datastruktur:
------------
- Förvaringsenheter med metadata och innehåll
- Historikspårning för alla ändringar
- Påminnelsesystem med tidsstämplar
- Kategorisering av varor för bättre organisation

Utvecklad med:
-------------
- Streamlit för användargränssnittet
- Pandas för dataanalys
- Plotly för visualiseringar
- JSON för datalagring
"""

# ===== IMPORTERA NÖDVÄNDIGA BIBLIOTEK =====
# streamlit (st) - Ett bibliotek för att skapa webbgränssnitt
# json - Används för att spara och läsa data i ett format som är lätt att läsa
# datetime - Hanterar datum och tid, används för utgångsdatum och tidsstämplar
# os - Hanterar filsystem, används för att kontrollera om filer existerar
# pandas (pd) - Kraftfullt bibliotek för dataanalys och datamanipulation
# plotly.express (px) - Skapar interaktiva grafer och diagram
# collections (Counter) - Hjälper till att räkna förekomster av objekt
# random - Används för att generera slumpmässiga värden i exempeldata
import streamlit as st
import json
from datetime import datetime, timedelta
import os
import plotly.express as px
from collections import Counter
import random
import time
from auth import login, logout, is_admin, is_logged_in, save_users, add_user, delete_user, list_users, change_password
from email_handler import send_expiration_notification, schedule_daily_notification, load_email_config, get_email_schedule_info, get_next_scheduled_time, format_weekdays, send_immediate_notification
import yaml
from database import (save_storage_data, load_storage_data, 
                     save_history_data, load_history_data,
                     save_reminders_data, load_reminders_data)

# Konfigurera pandas för att hantera framtida varningar
# Detta förhindrar varningsmeddelanden om datatypskonvertering
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)

# ===== INITIALISERA SESSIONSTILLSTÅND =====
# Sessionstillstånd är variabler som behåller sina värden mellan olika körningar av appen
# Om variablerna inte finns, skapa dem med tomma standardvärden

# storage_units: Lagrar information om alla förvaringsenheter (kylskåp, frys etc.)
# och deras innehåll i formatet:
# {
#   "Kökskylskåp": {
#     "type": "🧊 Kylskåp",
#     "contents": {
#       "Mjölk": {
#         "quantity": 1,
#         "category": "Mejeri",
#         "date_added": "2024-03-20",
#         "expiration_date": "2024-03-27"
#       }
#     }
#   }
# }
if 'storage_units' not in st.session_state:
    st.session_state.storage_units = {}

# expiration_reminders: Håller koll på påminnelser om utgångsdatum
# Sparar information om när användaren vill bli påmind om utgående varor
if 'expiration_reminders' not in st.session_state:
    st.session_state.expiration_reminders = {}

# item_history: Sparar historik över alla tillagda och borttagna varor
# Används för statistik och analys av användningsmönster
if 'item_history' not in st.session_state:
    st.session_state.item_history = []

# ===== DEFINIERA KONSTANTER =====
# Listor med fördefinierade val för användaren
# Emojis används för att göra gränssnittet mer visuellt tilltalande

# Lista över olika typer av förvaringsenheter
# Varje typ har en beskrivande emoji och ett namn
STORAGE_TYPES = [
    "🧊 Kylskåp",    # För kylda varor
    "❄️ Frys",       # För frysta varor
    "🏪 Skafferi",   # För torrvaror
    "🗄️ Skåp",      # För övriga förvaringsplatser
    "📦 Övrigt"      # För specialfall
]

# Lista över olika matkategorier
# Hjälper användaren att organisera och kategorisera sina varor
# Emojis gör det lättare att snabbt identifiera olika kategorier
FOOD_CATEGORIES = [
    "🥬 Frukt & Grönt",      # Färska grönsaker och frukt
    "🥩 Kött & Fisk",        # Kött, fisk och skaldjur
    "🥛 Mejeri",             # Mjölkprodukter
    "🥤 Drycker",            # Alla typer av drycker
    "🧂 Kryddor & Såser",    # Kryddor, såser och smaksättare
    "🍱 Matrester",          # Tillagad mat och rester
    "🍿 Snacks",             # Snacks och tilltugg
    "🍝 Spannmål & Pasta",   # Pasta, ris, bröd etc.
    "🧊 Frysta varor",       # Färdigfrysta produkter
    "📦 Övrigt"              # Övrigt som inte passar i andra kategorier
]


# ===== HJÄLPFUNKTIONER =====

def strip_emoji(text):
    """Ta bort emoji och extra mellanslag från text
    
    Denna funktion används för att rensa text från emojis och onödiga mellanslag.
    Detta är viktigt när vi ska använda texten som nyckel eller i statistik.
    
    Args:
        text (str): Texten som ska rensas, t.ex. "🥛 Mejeri"
    
    Returns:
        str: Rensad text, t.ex. "Mejeri"
    """
    return ' '.join(text.split()[1:]) if text.split() else text


def add_to_history(action, item_name, category, quantity, storage_unit, expired=False, exp_date=None, is_example=False, timestamp=None):
    """Lägg till en händelse i historiken"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create history entry
    history_entry = {
        'timestamp': timestamp,
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
    save_data()

    # Send immediate notification if enabled
    config = load_email_config()
    if config and not is_example:  # Don't send notifications for example data
        preferences = config['email']['notifications'].get('preferences', {})
        recipient = config['email']['notifications'].get('recipient')
        
        if ((action == 'added' and preferences.get('notify_added_items')) or 
            (action == 'removed' and preferences.get('notify_removed_items'))) and recipient:
            send_immediate_notification(action, history_entry, recipient)


def save_data():
    """Save all data to MongoDB"""
    save_storage_data(st.session_state.storage_units)
    save_history_data(st.session_state.item_history)
    save_reminders_data(st.session_state.expiration_reminders)
    
    # Clear expired items cache
    if 'expired_items' in st.session_state:
        del st.session_state.expired_items
    if 'expiring_warnings' in st.session_state:
        del st.session_state.expiring_warnings


def load_data():
    """Load all data from MongoDB"""
    try:
        # Load fresh data from database
        storage_data = load_storage_data()
        if storage_data:
            st.session_state.storage_units = storage_data
        else:
            st.session_state.storage_units = {}
            
        history_data = load_history_data()
        if history_data:
            st.session_state.item_history = history_data
        else:
            st.session_state.item_history = []
            
        reminders_data = load_reminders_data()
        if reminders_data:
            st.session_state.expiration_reminders = reminders_data
        else:
            st.session_state.expiration_reminders = {}

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.session_state.storage_units = {}
        st.session_state.expiration_reminders = {}
        st.session_state.item_history = []


def check_expiring_items():
    """Kontrollera varor som närmar sig utgångsdatum och utgångna varor"""
    # Always start with fresh lists
    expiration_warnings = []  # Lista för varor som snart går ut
    expired_items = []        # Lista för varor som redan har gått ut
    current_date = datetime.now().date()

    # Only check if there are storage units and they have contents
    if st.session_state.storage_units and any(unit.get('contents') for unit in st.session_state.storage_units.values()):
        # Gå igenom alla förvaringsenheter och deras innehåll
        for storage_name, storage_unit in st.session_state.storage_units.items():
            if not storage_unit.get('contents'):  # Skip if no contents
                continue
                
            for item_name, item_details in storage_unit['contents'].items():
                if 'expiration_date' in item_details:
                    try:
                        expiration_date = datetime.strptime(item_details['expiration_date'], "%Y-%m-%d").date()
                        days_remaining = (expiration_date - current_date).days

                        if days_remaining < 0:  # Varan har gått ut
                            expired_items.append({
                                'item': item_name,
                                'unit': storage_name,
                                'days': abs(days_remaining),
                                'exp_date': expiration_date.strftime("%Y-%m-%d"),
                                'category': item_details['category']
                            })
                        elif days_remaining <= 7:  # Varan går ut inom en vecka
                            reminder_key = f"{storage_name}_{item_name}"
                            if reminder_key not in st.session_state.expiration_reminders:
                                expiration_warnings.append({
                                    'item': item_name,
                                    'unit': storage_name,
                                    'days': days_remaining,
                                    'exp_date': expiration_date.strftime("%Y-%m-%d"),
                                    'key': reminder_key,
                                    'category': item_details['category']
                                })
                    except ValueError:
                        st.error(f"Ogiltigt datumformat för {item_name} i {storage_name}")
                        continue

    return expired_items, expiration_warnings


def populate_example_data():
    """Generera och lägg till exempeldata i appen"""
    # Kontrollera vilka enheter som redan finns (ignorera nummer i slutet av namn)
    existing_units = set()
    for unit_name in st.session_state.storage_units.keys():
        # Ta bort eventuella siffror och mellanslag från slutet av namnet
        base_name = unit_name.rstrip('0123456789 ')
        existing_units.add(base_name)
    
    # Standardenheter som kan läggas till
    base_units = {
        "Kökskylskåp": "🧊 Kylskåp",     # För vardagliga kylvaror
        "Köllarfrys": "❄️ Frys",         # För långtidsförvaring
        "Skafferi": "🏪 Skafferi",       # För torrvaror
        "Kryddskåp": "🗄️ Skåp"          # För kryddor och smaksättare
    }
    
    # Filtrera ut enheter som redan finns
    example_units = {}
    for name, type_ in base_units.items():
        if name not in existing_units:
            example_units[name] = type_
    
    if not example_units:
        st.warning("Alla standardenheter finns redan!")
        return
    
    # Lista över exempelvaror med tillhörande kategorier
    example_items = {
        "Mjölk": "🥛 Mejeri",            # Grundläggande mejeriprodukt
        "Ägg": "🥛 Mejeri",              # Protein och basvara
        "Ost": "🧀 Mejeri",              # Långhållbar mejeriprodukt
        "Köttfärs": "🥩 Kött & Fisk",    # Vanlig proteinkälla
        "Lax": "🥩 Kött & Fisk",         # Omega-3 rik fisk
        "Kyckling": "🥩 Kött & Fisk",    # Mager proteinkälla
        "Äpplen": "🥬 Frukt & Grönt",    # Hållbar frukt
        "Tomater": "🥬 Frukt & Grönt",   # Färsk grönsak
        "Sallad": "🥬 Frukt & Grönt",    # Kort hållbarhet
        "Bröd": "🍝 Spannmål & Pasta",   # Färskt bröd
        "Pasta": "🍝 Spannmål & Pasta",  # Torr pasta
        "Ris": "🍝 Spannmål & Pasta",    # Basmat
        "Juice": "🥤 Drycker",           # Färskpressad
        "Läsk": "🥤 Drycker",            # Lång hållbarhet
        "Ketchup": "🧂 Kryddor & Såser", # Öppnad flaska
        "Senap": "🧂 Kryddor & Såser",   # Kryddsäs
        "Glass": "🧊 Frysta varor",      # Dessert
        "Frysta ärtor": "🧊 Frysta varor", # Grönsaker
        "Chips": "🍿 Snacks",            # Tilltugg
        "Nötter": "🍿 Snacks",           # Proteinrikt snacks
        "Lasagne": "🍱 Matrester"        # Matlåda
    }
    
    # Generate a range of dates for the past 30 days
    current_date = datetime.now()
    past_dates = [
        (current_date - timedelta(days=x)).strftime("%Y-%m-%d %H:%M:%S") 
        for x in range(30)
    ]

    # Lägg till nya förvaringsenheter med innehåll
    for unit_name, unit_type in example_units.items():
        st.session_state.storage_units[unit_name] = {
            "type": unit_type,
            "contents": {},
            "is_example": True
        }
        
        # Lägg till 3-8 slumpmässiga varor i varje enhet
        for _ in range(random.randint(3, 8)):
            item_name = random.choice(list(example_items.keys()))
            category = example_items[item_name]
            
            # Generate random dates within the last 30 days
            add_timestamp = random.choice(past_dates)
            add_date = datetime.strptime(add_timestamp, "%Y-%m-%d %H:%M:%S")
            
            # 30% chans att varan är utgången
            if random.random() < 0.3:
                exp_date = add_date.date() + timedelta(days=random.randint(3, 10))  # Short expiry
            else:
                exp_date = add_date.date() + timedelta(days=random.randint(7, 30))  # Longer expiry
            
            # Lägg till i förvaringsenheten
            st.session_state.storage_units[unit_name]['contents'][item_name] = {
                "quantity": random.randint(1, 5),
                "category": category,
                "date_added": add_date.strftime("%Y-%m-%d"),
                "expiration_date": exp_date.strftime("%Y-%m-%d")
            }
            
            # Lägg till i historiken med varierande tidsstämplar
            add_to_history('added', item_name, category, random.randint(1, 5), unit_name, 
                          expired=False, exp_date=exp_date.strftime("%Y-%m-%d"), 
                          is_example=True, timestamp=add_timestamp)
            
            # Om varan är utgången, lägg till en "removed" händelse
            if exp_date < datetime.now().date():
                remove_timestamp = (datetime.strptime(add_timestamp, "%Y-%m-%d %H:%M:%S") + 
                                  timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d %H:%M:%S")
                add_to_history('removed', item_name, category, random.randint(1, 5), unit_name, 
                              expired=True, exp_date=exp_date.strftime("%Y-%m-%d"), 
                              is_example=True, timestamp=remove_timestamp)

    # Lägg till ytterligare historik för utgångna varor
    for _ in range(20):  # Skapa 20 historiska händelser
        item_name = random.choice(list(example_items.keys()))
        category = example_items[item_name]
        unit_name = random.choice(list(example_units.keys()))
        
        # Skapa datum för tillägg med varierande tidsstämplar
        add_timestamp = random.choice(past_dates)
        add_date = datetime.strptime(add_timestamp, "%Y-%m-%d %H:%M:%S")
        exp_date = add_date.date() + timedelta(days=random.randint(5, 15))
        remove_date = exp_date + timedelta(days=random.randint(1, 5))
        
        # Lägg till händelsen när varan lades till
        add_to_history('added', item_name, category, random.randint(1, 5), unit_name, 
                      expired=False, exp_date=exp_date.strftime("%Y-%m-%d"), 
                      is_example=True, timestamp=add_timestamp)
        
        # Lägg till händelsen när varan togs bort
        remove_timestamp = remove_date.strftime("%Y-%m-%d %H:%M:%S")
        add_to_history('removed', item_name, category, random.randint(1, 5), unit_name, 
                      expired=True, exp_date=exp_date.strftime("%Y-%m-%d"), 
                      is_example=True, timestamp=remove_timestamp)

    # Spara all data
    save_data()
    st.success("Exempel-data har lagts till!")


# Add this function near the top with other functions
@st.cache_data(ttl=300)  # Cacha resultatet i 5 minuter för bättre prestanda
def generate_statistics(history_data, storage_data, time_filter=None):
    """Generera statistik från historik- och lagringsdata
    
    Denna funktion analyserar användningsmönster och skapar statistik över:
    - Hur ofta olika varor används
    - Vilka kategorier som är mest aktiva
    - Utgångsmönster för olika varor
    - Generella användningstrender
    
    Args:
        history_data (list): Lista med historikdata för alla händelser
        storage_data (dict): Information om nuvarande förvaringsenheter
        time_filter (str, optional): Filtrera data baserat på tidsperiod
            - "Senaste veckan"
            - "Senaste månaden"
            - "Senaste året"
            - None (all data)
    
    Returns:
        tuple: (df, expired_df)
            - df: DataFrame med filtrerad historikdata
            - expired_df: DataFrame med information om utgångsdatum
    """
    if not history_data:
        return None

    # Konvertera historikdata till DataFrame för enklare analys
    df = pd.DataFrame(history_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])  # Konvertera tidsstämplar till datetime

    # Applicera tidsfilter om det är specificerat
    if time_filter:
        now = pd.Timestamp.now()
        if time_filter == "Senaste veckan":
            df = df[df['timestamp'] > now - pd.Timedelta(days=7)]
        elif time_filter == "Senaste månaden":
            df = df[df['timestamp'] > now - pd.Timedelta(days=30)]
        elif time_filter == "Senaste året":
            df = df[df['timestamp'] > now - pd.Timedelta(days=365)]

    # Skapa DataFrame för utgångsanalys
    current_date = pd.Timestamp.now().date()
    expired_df = pd.DataFrame()

    # Analysera utgångsdatum för alla nuvarande varor
    for unit_name, unit in storage_data.items():
        for item_name, details in unit['contents'].items():
            exp_date = pd.to_datetime(details['expiration_date']).date()
            expired_df = pd.concat([expired_df, pd.DataFrame([{
                'item': item_name,
                'category': strip_emoji(details['category']),
                'days_until_expiry': (exp_date - current_date).days,
                'storage_unit': unit_name,
                'quantity': details['quantity']
            }])], ignore_index=True)

    return df, expired_df


# At the very top of main.py, add permission checking
def check_auth():
    """Kontrollera autentisering och behörighet
    
    Stoppar körningen om användaren inte är inloggad.
    Visar endast inloggningsformuläret.
    """
    if not is_logged_in():
        login()
        st.stop()  # Stoppa körningen här om inte inloggad

# At the top of main.py, after imports

# Initialize MongoDB connection first
if 'mongodb_initialized' not in st.session_state:
    init_connection()
    st.session_state.mongodb_initialized = True

# Load data if not already loaded
if 'storage_units' not in st.session_state:
    load_data()

# Kontrollera autentisering först
check_auth()

# Visa utloggningsknapp i sidofältet
with st.sidebar:
    logout()
    
    # Varningar för utgångsdatum (synliga för alla inloggade)
    expired_items, expiring_warnings = check_expiring_items()
    
    # Visa alla varningar i en huvudexpander
    if expired_items or expiring_warnings:
        st.markdown("---")
        with st.expander("### 🚨 Utgångna varor! 🚨"):
            # Visa utgångna varor direkt i huvudexpandern
            if expired_items:
                for item in expired_items:
                    # Get the category emoji from the item's category
                    category_emoji = next((cat.split()[0] for cat in FOOD_CATEGORIES 
                                        if strip_emoji(cat) == strip_emoji(item['category'])), '📦')
                    st.error(
                        f"**{category_emoji} {item['item']}** är utgången sedan {item['days']} dagar!\n\n"
                        f"- Finns i: {item['unit']}\n"
                        f"- Utgångsdatum: {item['exp_date']}"
                    )
            else:
                st.info("Inga utgångna varor!")

        # Visa varor som snart går ut i en separat expander
        with st.expander("### ⏳ Varor som snart går ut"):
            if expiring_warnings:
                for item in expiring_warnings:
                    # Get the category emoji from the item's category
                    category_emoji = next((cat.split()[0] for cat in FOOD_CATEGORIES 
                                        if strip_emoji(cat) == strip_emoji(item['category'])), '📦')
                    st.warning(
                        f"**{category_emoji} {item['item']}** går ut om {item['days']} dagar!\n\n"
                        f"- Finns i: {item['unit']}\n"
                        f"- Utgångsdatum: {item['exp_date']}"
                    )
            else:
                st.info("Inga varor på väg att gå ut!")
    
    # Endast administratörer kan lägga till förvaringsenheter
    if is_admin():
        st.markdown("---")
        st.header("Lägg till ny förvaringsenhet")
        unit_name = st.text_input("Namn (t.ex. Kökskylskåp)")
        unit_type = st.selectbox("Typ", STORAGE_TYPES)
        
        if st.button("Lägg till förvaringsenhet", key="add_unit"):
            if unit_name:
                if unit_name not in st.session_state.storage_units:
                    st.session_state.storage_units[unit_name] = {
                        "type": unit_type,
                        "contents": {}
                    }
                    save_data()
                    st.success(f"Lade till {unit_name}")
                else:
                    st.error("En förvaringsenhet med detta namn finns redan!")

# Huvudinnehåll
st.title("🧊 Matförvaring")

# Create tabs list based on user role
tabs = ["📦 Förvaring", "📊 Statistik"]
if is_admin():
    tabs.append("⚙️ Admin")

# Create tabs
selected_tab = st.tabs(tabs)

# ===== ADMINFLIK =====
if is_admin() and len(selected_tab) > 2:
    with selected_tab[2]:
        st.title("⚙️ Administratörsinställningar")
        st.warning("🚨Varning🚨: Dessa funktioner kan skapa instabilitet och påverka all lagrad data!")

        with st.expander("️ Inställningar för data"):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Hantera exempeldata")
                if st.button("Lägg till exempel-data", type="secondary"):
                    populate_example_data()

                if st.button("Rensa endast exempeldata", type="secondary"):
                    # Ta bort förvaringsenheter markerade som exempel
                    st.session_state.storage_units = {
                        k: v for k, v in st.session_state.storage_units.items()
                        if not v.get('is_example', False)
                    }
                    # Ta bort historik markerad som exempel
                    st.session_state.item_history = [
                        item for item in st.session_state.item_history
                        if not item.get('is_example', False)
                    ]
                    save_data()
                    st.success("Exempeldata har rensats!")

            with col2:
                st.subheader("Rensa specifik data")
                if st.button("Rensa förvaringsenheter", type="secondary"):
                    st.session_state.storage_units = {}
                    save_data()
                    st.success("Alla förvaringsenheter har rensats!")

                if st.button("Rensa påminnelser", type="secondary"):
                    st.session_state.expiration_reminders = {}
                    save_data()
                    st.success("Alla påminnelser har rensats!")

                if st.button("Rensa historik", type="secondary"):
                    st.session_state.item_history = []
                    save_data()
                    st.success("All historik har rensats!")

            # Rensa all data (med extra varning)
            st.subheader("Rensa all data")
            clear_all = st.button("Rensa ALL data", type="secondary")
            confirm = st.checkbox("Jag förstår att detta kommer radera ALL data permanent")

            if clear_all and confirm:
                # Rensa all data
                st.session_state.storage_units = {}
                st.session_state.expiration_reminders = {}
                st.session_state.item_history = []
                save_data()
                st.success("All data har rensats!")
                time.sleep(1)  # Ge användaren tid att se meddelandet
                st.rerun()
            elif clear_all and not confirm:
                st.error("Du måste bekräfta att du vill radera all data genom att markera checkboxen")

            st.markdown("---")
        
        # Användarhantering
        with st.expander("👥 Användarhantering"):
        
            # Visa befintliga användare
            users = list_users()
            if users:
                st.write("### Befintliga användare")
                for username, data in users.items():
                    st.write(f"- {username} ({data['role']})")

            # Lägg till ny användare
            st.subheader("Lägg till ny användare")
            new_username = st.text_input("Användarnamn", key="new_user_name")
            new_password = st.text_input("Lösenord", type="password", key="new_user_pass")
            new_role = st.selectbox(
                "Roll",
                options=['user', 'admin'],
                key="new_user_role"
            )

            if st.button("Skapa användare"):
                if new_username and new_password:
                    success, message = add_user(new_username, new_password, new_role)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Både användarnamn och lösenord krävs")
            
            # In the admin panel, under user management
            st.subheader("Ändra lösenord")
            user_to_change = st.selectbox(
                "Välj användare",
                options=list(users.keys()),
                key="user_to_change_pw"
            )

            new_password = st.text_input("Nytt lösenord", type="password", key="new_password")
            confirm_password = st.text_input("Bekräfta nytt lösenord", type="password", key="confirm_password")

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

            # Ta bort användare
            st.subheader("Ta bort användare")
            user_to_delete = st.selectbox(
                "Välj användare att ta bort",
                options=[u for u in users.keys() if u != 'admin'],
                key="user_to_delete"
            )

            # Move checkbox before the button
            confirm_delete = st.checkbox("Jag är säker på att jag vill ta bort denna användare", key="confirm_delete_user")

            if st.button("Ta bort användare"):
                if user_to_delete:
                    if confirm_delete:
                        success, message = delete_user(user_to_delete)
                        if success:
                            st.success(message)
                            st.rerun()  # Refresh to update user list
                        else:
                            st.error(message)
                    else:
                        st.warning("Bekräfta borttagning genom att markera checkboxen")

            st.markdown("---")

        # Email notifications section
        with st.expander("📧 Email Notifications"):
            # Show current email settings
            config = load_email_config()
            if config and config['email']['notifications'].get('recipient'):
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"Email-notifieringar är aktiva för: {config['email']['notifications']['recipient']}")
                    
                    # Always show last sent info
                    last_sent, next_send = get_email_schedule_info()
                    schedule = config['email']['notifications'].get('schedule', {
                        'weekdays': list(range(7)),
                        'time': "08:00"
                    })
                    
                    if last_sent:
                        current_time = datetime.now()
                        days_ago = (current_time - last_sent).days
                        
                        if days_ago == 0:
                            if last_sent.date() == current_time.date():
                                sent_text = f"idag kl {last_sent.strftime('%H:%M')}"
                            else:
                                sent_text = f"igår kl {last_sent.strftime('%H:%M')}"
                        else:
                            sent_text = f"för {days_ago} dagar sedan (kl {last_sent.strftime('%H:%M')})"
                        
                        st.info(f"Senaste email skickades {sent_text}")
                        
                        if next_send:
                            days_until = (next_send.date() - current_time.date()).days
                            if days_until == 0:
                                next_text = f"idag kl {next_send.strftime('%H:%M')}"
                            elif days_until == 1:
                                next_text = f"imorgon kl {next_send.strftime('%H:%M')}"
                            else:
                                next_text = f"på {next_send.strftime('%A').lower()} kl {next_send.strftime('%H:%M')}"
                            
                            st.info(f"Nästa email skickas {next_text}")
                            st.info(f"Schemalagt att skickas {format_weekdays(schedule['weekdays'])} kl {schedule['time']}")
                    else:
                        st.info("Inget email har skickats än")
                        st.info("Nästa email skickas vid nästa kontroll")

                with col2:
                    # Button to reset last sent date
                    if st.button("Återställ senaste skickad"):
                        config['email']['notifications']['last_sent'] = None
                        with open('email_config.yml', 'w', encoding='utf-8') as file:
                            yaml.dump(config, file)
                        st.success("Återställt! Nästa kontroll kommer skicka email.")
                        st.rerun()

                    # Test button that ignores the daily limit
                    if st.button("Skicka test-email"):
                        expired_items, expiring_warnings = check_expiring_items()
                        if expired_items or expiring_warnings:
                            all_items = expired_items + expiring_warnings
                            # Create a temporary copy of the config for testing
                            test_config = config.copy()
                            test_config['email']['notifications']['last_sent'] = None
                            with open('email_config.yml', 'w', encoding='utf-8') as file:
                                yaml.dump(test_config, file)

                            if send_expiration_notification(all_items, config['email']['notifications']['recipient']):
                                st.success("Test-email skickat!")

                            # Restore the original last_sent date
                            config['email']['notifications']['last_sent'] = last_sent
                            with open('email_config.yml', 'w', encoding='utf-8') as file:
                                yaml.dump(config, file)
                        else:
                            st.info("Inga varor att notifiera om")

                # Email setup
                st.subheader("Email-inställningar")
                email_recipient = st.text_input("Email för notifieringar", key="email_notifications")

                # Vilka ändringar att notifiera om
                # Checkboxes for different happenings in the app that would warrant a notification,
                # to be chosen by the admin.

                # Add weekday selection
                weekday_options = {
                    "Alla dagar": list(range(7)),
                    "Vardagar": list(range(5)),
                    "Helger": [5, 6],
                    "Anpassat": "custom"
                }
                selected_schedule = st.selectbox(
                    "Skicka email på",
                    options=list(weekday_options.keys()),
                    key="weekday_schedule"
                )

                if selected_schedule == "Anpassat":
                    weekdays = []
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.checkbox("Måndag"): weekdays.append(0)
                        if st.checkbox("Tisdag"): weekdays.append(1)
                        if st.checkbox("Onsdag"): weekdays.append(2)
                        if st.checkbox("Torsdag"): weekdays.append(3)
                    with col2:
                        if st.checkbox("Fredag"): weekdays.append(4)
                        if st.checkbox("Lördag"): weekdays.append(5)
                        if st.checkbox("Söndag"): weekdays.append(6)
                else:
                    weekdays = weekday_options[selected_schedule]

                # Add time selection
                time_str = st.time_input(
                    "Skicka klockan",
                    value=datetime.strptime("08:00", "%H:%M"),
                    key="email_time"
                ).strftime("%H:%M")

                # Add after time selection in the email notifications section
                st.subheader("Notifieringsinställningar")
                col1, col2 = st.columns(2)

                with col1:
                    notify_expired = st.checkbox(
                        "Utgångna varor", 
                        value=config.get('email', {}).get('notifications', {}).get('preferences', {}).get('notify_expired', True),
                        help="Skicka notifieringar om varor som har gått ut"
                    )
                    
                    notify_expiring_soon = st.checkbox(
                        "Varor som snart går ut", 
                        value=config.get('email', {}).get('notifications', {}).get('preferences', {}).get('notify_expiring_soon', True),
                        help="Skicka notifieringar om varor som snart går ut"
                    )
                    
                    notify_low_quantity = st.checkbox(
                        "Lågt antal", 
                        value=config.get('email', {}).get('notifications', {}).get('preferences', {}).get('notify_low_quantity', False),
                        help="Skicka varning när antalet av en vara är lågt"
                    )

                with col2:
                    notify_removed_items = st.checkbox(
                        "Borttagna varor", 
                        value=config.get('email', {}).get('notifications', {}).get('preferences', {}).get('notify_removed_items', False),
                        help="Skicka notifieringar när varor tas bort"
                    )
                    
                    notify_added_items = st.checkbox(
                        "Tillagda varor", 
                        value=config.get('email', {}).get('notifications', {}).get('preferences', {}).get('notify_added_items', False),
                        help="Skicka notifieringar när nya varor läggs till"
                    )

                # Additional settings that appear based on checkboxes
                if notify_expiring_soon:
                    expiring_soon_days = st.number_input(
                        "Antal dagar innan utgång för varning",
                        min_value=1,
                        max_value=30,
                        value=config.get('email', {}).get('notifications', {}).get('preferences', {}).get('expiring_soon_days', 7),
                        help="Skicka varning när vara går ut inom detta antal dagar"
                    )
                else:
                    expiring_soon_days = 7

                if notify_low_quantity:
                    low_quantity_threshold = st.number_input(
                        "Gräns för lågt antal",
                        min_value=1,
                        max_value=10,
                        value=config.get('email', {}).get('notifications', {}).get('preferences', {}).get('low_quantity_threshold', 2),
                        help="Skicka varning när antalet är lägre än detta"
                    )
                else:
                    low_quantity_threshold = 2

                # Update the preferences when activating notifications
                notification_preferences = {
                    'notify_expired': notify_expired,
                    'notify_expiring_soon': notify_expiring_soon,
                    'notify_low_quantity': notify_low_quantity,
                    'notify_removed_items': notify_removed_items,
                    'notify_added_items': notify_added_items,
                    'expiring_soon_days': expiring_soon_days,
                    'low_quantity_threshold': low_quantity_threshold
                }

                # Add a save settings button
                if st.button("Spara inställningar"):
                    if config and config['email']['notifications'].get('recipient'):
                        # Update only the preferences in the existing config
                        config['email']['notifications']['preferences'] = notification_preferences
                        try:
                            with open('email_config.yml', 'w', encoding='utf-8') as file:
                                yaml.dump(config, file)
                            st.success("Inställningar sparade!")
                            time.sleep(0.5)  # Give a moment for the success message to be visible
                            st.rerun()  # Add this line to rerun the app
                        except Exception as e:
                            st.error(f"Kunde inte spara inställningar: {str(e)}")
                    else:
                        st.error("Email-notifieringar måste vara aktiverade först")

                # Existing activation button
                if st.button("Aktivera email-notifieringar"):
                    if email_recipient:
                        if schedule_daily_notification(email_recipient, weekdays, time_str, notification_preferences):
                            st.success("Email-notifieringar aktiverade!")
                            # Send first notification immediately
                            expired_items, expiring_warnings = check_expiring_items()
                            if expired_items or expiring_warnings:
                                all_items = expired_items + expiring_warnings
                                if send_expiration_notification(all_items, email_recipient):
                                    st.success("Första notifieringen skickad!")
                        else:
                            st.error("Kunde inte aktivera email-notifieringar")
                    else:
                        st.error("Ange en email-adress")

                # Add button to manually send notification
                if st.button("Skicka notifiering nu"):
                    expired_items, expiring_warnings = check_expiring_items()
                    if expired_items or expiring_warnings:
                        all_items = expired_items + expiring_warnings
                        
                        # Create a temporary copy of the config for immediate sending
                        temp_config = config.copy()
                        temp_config['email']['notifications']['last_sent'] = None  # Reset last sent time
                        
                        with open('email_config.yml', 'w', encoding='utf-8') as file:
                            yaml.dump(temp_config, file)
                        
                        # Try to send notification
                        try:
                            if send_expiration_notification(all_items, config['email']['notifications']['recipient']):
                                st.success("Notifiering skickad!")
                            else:
                                st.error("Kunde inte skicka notifiering")
                        except Exception as e:
                            st.error(f"Fel vid skickande av notifiering: {str(e)}")
                            
                        # Restore original config
                        with open('email_config.yml', 'w', encoding='utf-8') as file:
                            yaml.dump(config, file)
                    else:
                        st.info("Inga varor att notifiera om")
                        # Debug information
                        st.write("Debug info:")
                        st.write(f"Antal utgångna varor: {len(expired_items)}")
                        st.write(f"Antal varor som snart går ut: {len(expiring_warnings)}")

# ===== FÖRVARINGSFLIK =====
with selected_tab[0]:
    st.title("📦 Förvarade Varor")
    
    # Check if there are any storage units
    if not st.session_state.storage_units:
        st.warning("Inga förvaringsenheter finns tillgängliga. Be en administratör att lägga till förvaringsenheter.")
        st.stop()  # Stop execution here since there's nothing else to show
    
    # Väljare för förvaringsenhet
    selected_unit = st.selectbox(
        "Välj förvaringsenhet",
        options=list(st.session_state.storage_units.keys()),
        key="unit_selector_1"
    )
    
    # Visa innehåll och kontroller för vald enhet
    if selected_unit:
        unit = st.session_state.storage_units[selected_unit]
        
        # Sektion för att lägga till nya varor
        with st.expander("Lägg till ny vara"):
            st.subheader(f"{selected_unit} ({strip_emoji(unit['type'])})")
            
            # Val mellan att skriva in ny vara eller välja från tidigare
            input_method = st.radio(
                "Välj inmatningsmetod",
                ["Välj från tidigare varor", "Skriv in ny vara"],
                horizontal=True,
                key="input_method_1"
            )

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if input_method == "Skriv in ny vara":
                    new_item = st.text_input("Lägg till vara", key="new_item_text_1")
                else:
                    # Get unique items from history
                    previous_items = set()
                    for history_item in st.session_state.item_history:
                        previous_items.add(history_item['item'])
                    # Add current items from all storage units
                    for storage_unit in st.session_state.storage_units.values():
                        for item in storage_unit['contents'].keys():
                            previous_items.add(item)

                    if previous_items:
                        new_item = st.selectbox(
                            "Välj vara",
                            options=sorted(list(previous_items)),
                            key="previous_items_1"
                        )
                    else:
                        st.info("Inga tidigare varor att välja från.")
                        new_item = st.text_input("Lägg till vara", key="new_item_text_1")
            with col2:
                quantity = st.number_input("Antal", min_value=1, value=1, key="quantity_1")
            with col3:
                category = st.selectbox("Kategori", FOOD_CATEGORIES, key="category_selector_1")

            exp_date = st.date_input(
                "Utgångsdatum",
                min_value=datetime.now().date(),
                value=datetime.now().date() + timedelta(days=7),
                key="exp_date_1"
            )

            if st.button("Lägg till vara", key="add_item_1"):
                if new_item:
                    unit['contents'][new_item] = {
                        "quantity": quantity,
                        "category": category,
                        "date_added": datetime.now().strftime("%Y-%m-%d"),
                        "expiration_date": exp_date.strftime("%Y-%m-%d")
                    }
                    add_to_history('added', new_item, category, quantity, selected_unit)
                    save_data()
                    st.success(f"Lade till {quantity} {new_item}")

        # Visa innehåll
        if unit['contents']:
            st.write("### 📦 Innehåll")
            for item, details in unit['contents'].items():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                with col1:
                    st.write(f"{item} ({strip_emoji(details['category'])})")
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

                # Add quantity selector after each item's row
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
                                if remove_quantity == details['quantity']:
                                    # Remove entire item
                                    add_to_history(
                                        'removed', 
                                        item, 
                                        details['category'], 
                                        remove_quantity, 
                                        selected_unit,
                                        expired=datetime.strptime(details['expiration_date'], "%Y-%m-%d").date() < datetime.now().date(),
                                        exp_date=details['expiration_date']
                                    )
                                    del unit['contents'][item]
                                else:
                                    # Update quantity
                                    add_to_history(
                                        'removed', 
                                        item, 
                                        details['category'], 
                                        remove_quantity, 
                                        selected_unit,
                                        expired=datetime.strptime(details['expiration_date'], "%Y-%m-%d").date() < datetime.now().date(),
                                        exp_date=details['expiration_date']
                                    )
                                    unit['contents'][item]['quantity'] -= remove_quantity
                                save_data()
                                # Clear the session state to hide the quantity selector
                                del st.session_state[f"show_quantity_selector_{item}"]
                                st.rerun()
                            if st.button("Avbryt", key=f"cancel_remove_{item}"):
                                del st.session_state[f"show_quantity_selector_{item}"]
                                st.rerun()
        else:
            st.info("📭 Inga varor tillagda än!")

        # Ta bort förvaringsenhet
        if is_admin():
            if st.button("Ta bort förvaringsenhet", type="secondary"):
                try:
                    # Remove the storage unit
                    del st.session_state.storage_units[selected_unit]
                    
                    # Clear expiration reminders for this unit
                    st.session_state.expiration_reminders = {
                        k: v for k, v in st.session_state.expiration_reminders.items()
                        if not k.startswith(f"{selected_unit}_")
                    }
                    
                    # Save changes to database
                    save_data()
                    
                    # Clear cache and rerun
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting storage unit: {str(e)}")

# ===== STATISTIKFLIK =====
with selected_tab[1]:
    st.title("📊 Statistik och Analys")
    
    if not st.session_state.item_history:
        st.info("Ingen historik tillgänglig än. Börja med att lägga till och ta bort varor!")
    else:
        # Låt användaren välja tidsperiod för statistiken
        time_period = st.selectbox(
            "Välj tidsperiod",
            ["Senaste veckan", "Senaste månaden", "Senaste året", "Allt"]
        )
        
        # Generera statistik endast när användaren klickar på knappen
        # Detta sparar resurser och gör appen snabbare
        if st.button("Visa statistik", type="primary"):
            with st.spinner("Genererar statistik..."):
                # Hämta filtrerad data för vald tidsperiod
                df, expired_df = generate_statistics(
                    st.session_state.item_history,
                    st.session_state.storage_units,
                    time_period if time_period != "Allt" else None
                )
                
                # ===== AKTIVITETSSTATISTIK =====
                with st.expander("Aktivitetsstatistik"):
                    st.write("### Aktivitetsstatistik")
                    
                    # Cirkeldiagram över mest aktiva kategorier
                    st.subheader("Mest aktiva kategorier")
                    category_activity = df['category'].value_counts()
                    fig1 = px.pie(
                        values=category_activity.values,
                        names=category_activity.index,
                        title="Aktivitet per kategori"
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                    # Stapeldiagram över mest tillagda varor
                    st.subheader("Mest tillagda varor")
                    added_items = df[df['action'] == 'added']['item'].value_counts().head(10)
                    fig2 = px.bar(
                        data_frame=pd.DataFrame({
                            'Vara': added_items.index,
                            'Antal': added_items.values
                        }),
                        x='Vara',
                        y='Antal',
                        title="Topp 10 tillagda varor"
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    # Stapeldiagram över aktivitet över tid
                    st.subheader("Aktivitet över tid")
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    daily_activity = df.groupby(df['timestamp'].dt.date).size().reset_index()
                    daily_activity.columns = ['Datum', 'Antal']

                    fig3 = px.bar(
                        daily_activity,
                        x='Datum',
                        y='Antal',
                        title="Daglig aktivitet",
                        labels={'Datum': 'Datum', 'Antal': 'Antal händelser'}
                    )
                    fig3.update_layout(
                        bargap=0.2,
                        xaxis_tickangle=-45,
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                    # Stapeldiagram över mest använda varor
                    st.subheader("Mest använda varor")
                    removed_items = df[
                        (df['action'] == 'removed') & 
                        (df['expired'] == False)
                    ]['item'].value_counts().head(10)

                    if not removed_items.empty:
                        fig4 = px.bar(
                            data_frame=pd.DataFrame({
                                'Vara': removed_items.index,
                                'Antal': removed_items.values
                            }),
                            x='Vara',
                            y='Antal',
                            title="Topp 10 använda varor (ej utgångna)"
                        )
                        st.plotly_chart(fig4, use_container_width=True)
                    else:
                        st.info("Ingen data om använda varor tillgänglig")
                
                # ===== ÖVRIG STATISTIK =====
                with st.expander("Ytterligare statistik"):
                    st.write("### Ytterligare statistik")
                    col3, col4, col5 = st.columns(3)

                    # Visa sammanfattande mätvärden
                    with col3:
                        total_items = len(df[df['action'] == 'added'])
                        st.metric(
                            "Totalt antal tillagda varor",  # Totalt antal varor som lagts till
                            total_items
                        )

                    with col4:
                        # Count only non-expired removals
                        used_items = len(df[
                            (df['action'] == 'removed') & 
                            (df['expired'] == False)
                        ])
                        st.metric(
                            "Använda varor (ej utgångna)",
                            used_items
                        )

                    with col5:
                        # Count expired removals separately
                        expired_removals = len(df[
                            (df['action'] == 'removed') & 
                            (df['expired'] == True)
                        ])
                        st.metric(
                            "Utgångna varor",
                            expired_removals
                        )

                # ===== UTGÅNGSSTATISTIK =====
                with st.expander("Utgångsstatistik"):
                    st.markdown("---")
                    st.header("📅 Statistik över utgångna varor")

                    if not expired_df.empty:
                        # Stapeldiagram över varor nära utgång
                        st.subheader("Varor nära utgångsdatum")
                        near_expiry = expired_df[expired_df['days_until_expiry'] > 0].sort_values('days_until_expiry').head(10)
                        if not near_expiry.empty:
                            fig5 = px.bar(
                                data_frame=near_expiry,
                                x='item',
                                y='days_until_expiry',
                                color='category',
                                title="Dagar till utgång för varor",
                                labels={'item': 'Vara', 'days_until_expiry': 'Dagar till utgång'}
                            )
                            st.plotly_chart(fig5, use_container_width=True)
                        else:
                            st.info("Inga varor närmar sig utgångsdatum")

                        # Cirkeldiagram över utgångna varor per kategori
                        expired_by_category = expired_df[expired_df['days_until_expiry'] < 0].groupby('category').size()
                        if not expired_by_category.empty:
                            st.subheader("Kategorier med utgångna varor")
                            fig6 = px.pie(
                                values=expired_by_category.values,
                                names=expired_by_category.index,
                                title="Fördelning av utgångna varor per kategori"
                            )
                            st.plotly_chart(fig6, use_container_width=True)

                        # Stapeldiagram över genomsnittlig hållbarhet
                        st.subheader("Genomsnittlig hållbarhet")
                        avg_shelf_life = expired_df.groupby('category')['days_until_expiry'].mean().sort_values()
                        if not avg_shelf_life.empty:
                            fig7 = px.bar(
                                x=avg_shelf_life.index,
                                y=avg_shelf_life.values,
                                title="Genomsnittlig hållbarhet per kategori (dagar)",
                                labels={'x': 'Kategori', 'y': 'Dagar'}
                            )
                            st.plotly_chart(fig7, use_container_width=True)

                        # Stapeldiagram över mest utgångna varor
                        expired_history = df[
                            (df['action'] == 'removed') &
                            (df['expired'] == True)
                        ]['item'].value_counts().head(10)

                        if not expired_history.empty:
                            st.subheader("Mest utgångna varor")
                            fig8 = px.bar(
                                data_frame=pd.DataFrame({
                                    'Vara': expired_history.index,
                                    'Antal': expired_history.values
                                }),
                                x='Vara',
                                y='Antal',
                                title="Topp 10 varor som ofta går ut"
                            )
                            st.plotly_chart(fig8, use_container_width=True)

                        # Sammanfattning av utgångna varor
                        st.subheader("Sammanfattning av utgångna varor")
                        col8, col9, col10 = st.columns(3)

                        with col8:
                            currently_expired = len(expired_df[expired_df['days_until_expiry'] < 0])
                            st.metric(
                                "Antal utgångna varor just nu",
                                currently_expired
                            )

                        with col9:
                            near_expiry_count = len(expired_df[
                                (expired_df['days_until_expiry'] >= 0) &
                                (expired_df['days_until_expiry'] <= 7)])
                            st.metric(
                                "Varor som går ut inom 7 dagar",
                                near_expiry_count
                            )

                        with col10:
                            positive_days = expired_df[expired_df['days_until_expiry'] > 0]
                            if not positive_days.empty:
                                avg_days_to_expiry = int(positive_days['days_until_expiry'].mean())
                                st.metric(
                                    "Genomsnittlig tid till utgång",
                                    f"{avg_days_to_expiry} dagar"
                                )
                            else:
                                st.metric(
                                    "Genomsnittlig tid till utgång",
                                    "0 dagar"
                                )
                    else:
                        st.info("Ingen utgångsdatumdata tillgänglig än.")

