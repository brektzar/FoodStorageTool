"""
Email notification handler för Matförvaringsappen
Hanterar alla email-relaterade funktioner
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import yaml
from datetime import datetime, timedelta

# Load email configuration
def load_email_config():
    """Load email configuration from YAML file and Streamlit secrets"""
    try:
        with open('email_config.yml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            # Add sensitive data from Streamlit secrets
            config['email']['app_password'] = st.secrets["email"]["app_password"]
            config['email']['sender'] = st.secrets["email"]["sender"]
            return config
    except FileNotFoundError:
        st.error("Email configuration file (email_config.yml) not found!")
        return None

def send_expiration_notification(items, recipient_email=None):
    """Send email notification about expiring items"""
    config = load_email_config()
    if not config:
        st.error("Kunde inte ladda email-konfiguration")
        return False

    # Get recipient from secrets if not provided
    if recipient_email is None:
        recipient_email = st.secrets["email"]["recipient"]

    # Get notification preferences
    preferences = config['email']['notifications'].get('preferences', {
        'notify_expired': True,
        'notify_expiring_soon': True,
        'notify_low_quantity': False,
        'notify_removed_items': False,
        'notify_added_items': False,
        'expiring_soon_days': 7,
        'low_quantity_threshold': 2
    })

    # Debug information
    st.write("Debug info:")
    st.write(f"Antal varor före filtrering: {len(items)}")
    st.write(f"Notifieringsinställningar: {preferences}")

    # Filter and categorize items based on preferences
    expired_items = []
    expiring_items = []
    low_quantity_items = []
    
    for item in items:
        # Check expired and expiring items
        if item['days'] < 0 and preferences.get('notify_expired', True):
            expired_items.append(item)
        elif item['days'] >= 0 and preferences.get('notify_expiring_soon', True):
            if item['days'] <= preferences.get('expiring_soon_days', 7):
                expiring_items.append(item)
        
        # Check low quantity items
        if preferences.get('notify_low_quantity', False):
            if item.get('quantity', 0) <= preferences.get('low_quantity_threshold', 2):
                low_quantity_items.append(item)

    # If no items to notify about after filtering, return early
    if not (expired_items or expiring_items or low_quantity_items):
        st.info("Inga varor att notifiera om efter filtrering")
        return True

    # Create message
    msg = MIMEMultipart()
    msg['From'] = config['email']['sender']
    msg['To'] = recipient_email
    msg['Subject'] = "Matförvaring - Status"

    # Create email body
    body = """
    <html>
    <body>
    <h2>Matförvaring - Statusrapport</h2>
    """

    # Add expired items
    if expired_items and preferences.get('notify_expired', True):
        body += "<h3>🚨 Utgångna varor:</h3><ul>"
        for item in expired_items:
            body += f"""
            <li><strong>{item['item']}</strong>
                <ul>
                    <li>Utgången sedan: {abs(item['days'])} dagar</li>
                    <li>Finns i: {item['unit']}</li>
                    <li>Utgångsdatum: {item['exp_date']}</li>
                    <li>Antal: {item.get('quantity', 'Okänt')}</li>
                </ul>
            </li>
            """
        body += "</ul>"

    # Add items about to expire
    if expiring_items and preferences.get('notify_expiring_soon', True):
        body += "<h3>⚠️ Varor som snart går ut:</h3><ul>"
        for item in expiring_items:
            body += f"""
            <li><strong>{item['item']}</strong>
                <ul>
                    <li>Går ut om: {item['days']} dagar</li>
                    <li>Finns i: {item['unit']}</li>
                    <li>Utgångsdatum: {item['exp_date']}</li>
                    <li>Antal: {item.get('quantity', 'Okänt')}</li>
                </ul>
            </li>
            """
        body += "</ul>"

    # Add low quantity items
    if low_quantity_items and preferences.get('notify_low_quantity', False):
        body += f"<h3>📉 Varor med lågt antal (under {preferences['low_quantity_threshold']}):</h3><ul>"
        for item in low_quantity_items:
            body += f"""
            <li><strong>{item['item']}</strong>
                <ul>
                    <li>Antal: {item.get('quantity', 'Okänt')}</li>
                    <li>Finns i: {item['unit']}</li>
                    <li>Utgångsdatum: {item['exp_date']}</li>
                </ul>
            </li>
            """
        body += "</ul>"

    body += """
    <p>Med vänliga hälsningar,<br>Din Matförvaringsapp</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        # Create secure SSL/TLS connection
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(config['email']['sender'], config['email']['app_password'])
        
        # Send email
        server.send_message(msg)
        server.quit()

        # Always update last sent date and time
        config['email']['notifications']['last_sent'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('email_config.yml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file)

        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def get_next_scheduled_time(weekdays, time_str):
    """Calculate next scheduled send time based on weekdays and time
    
    Args:
        weekdays (list): List of weekday numbers (0=Monday, 6=Sunday)
        time_str (str): Time in 24-hour format ("HH:MM")
    
    Returns:
        datetime: Next scheduled send time
    """
    current = datetime.now()
    scheduled_time = datetime.strptime(time_str, "%H:%M").time()
    
    # Start with today
    next_date = current.date()
    
    # If today is allowed but time has passed, or if today is not allowed,
    # find the next allowed day
    if (current.weekday() not in weekdays or 
        (current.weekday() in weekdays and current.time() > scheduled_time)):
        # Find next allowed weekday
        for _ in range(8):  # Check up to 7 days ahead plus today
            next_date += timedelta(days=1)
            if next_date.weekday() in weekdays:
                break
    
    # Combine date with scheduled time
    next_datetime = datetime.combine(next_date, scheduled_time)
    return next_datetime

def schedule_daily_notification(recipient_email, weekdays=None, time_str="08:00", preferences=None):
    """Schedule notifications with specific weekdays and time
    
    Args:
        recipient_email (str): Email address to send notifications to
        weekdays (list, optional): List of weekday numbers (0=Monday, 6=Sunday)
        time_str (str, optional): Time in 24-hour format ("HH:MM")
        preferences (dict, optional): Notification preferences
    """
    config = load_email_config()
    if not config:
        return False

    if weekdays is None:
        weekdays = list(range(7))  # All days by default
        
    if preferences is None:
        preferences = {
            'notify_expired': True,
            'notify_expiring_soon': True,
            'notify_low_quantity': False,
            'notify_removed_items': False,
            'notify_added_items': False,
            'expiring_soon_days': 7,
            'low_quantity_threshold': 2
        }

    # Save email preferences
    config['email']['notifications'] = {
        'recipient': recipient_email,
        'frequency': 'daily',
        'last_sent': None,
        'schedule': {
            'weekdays': weekdays,
            'time': time_str
        },
        'preferences': preferences
    }

    try:
        with open('email_config.yml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file)
        return True
    except Exception as e:
        st.error(f"Failed to save email preferences: {str(e)}")
        return False

def get_email_schedule_info():
    """Get information about email schedule"""
    config = load_email_config()
    if not config or not config['email']['notifications'].get('last_sent'):
        return None, None

    # Get schedule settings
    schedule = config['email']['notifications'].get('schedule', {
        'weekdays': list(range(7)),
        'time': "08:00"
    })
    
    # Parse last sent date and time with full timestamp
    last_sent = config['email']['notifications']['last_sent']
    if isinstance(last_sent, str):
        try:
            # Try parsing with seconds
            last_sent = datetime.strptime(last_sent, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # Try parsing without seconds
                last_sent = datetime.strptime(last_sent, "%Y-%m-%d %H:%M")
            except ValueError:
                # If all else fails, try just the date
                last_sent = datetime.strptime(last_sent, "%Y-%m-%d")
    
    # Calculate next send time
    next_send = get_next_scheduled_time(
        schedule['weekdays'],
        schedule['time']
    )
    
    return last_sent, next_send

def format_weekdays(weekdays):
    """Format weekday numbers to Swedish day names
    
    Args:
        weekdays (list): List of weekday numbers (0=Monday, 6=Sunday)
    
    Returns:
        str: Formatted weekday string
    """
    day_names = ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"]
    if len(weekdays) == 7:
        return "alla dagar"
    elif len(weekdays) == 5 and all(d < 5 for d in weekdays):
        return "vardagar"
    else:
        return ", ".join(day_names[d] for d in sorted(weekdays))

def send_immediate_notification(action, item_details, recipient_email):
    """Send immediate notification when items are added or removed"""
    config = load_email_config()
    if not config:
        st.error("Kunde inte ladda email-konfiguration")
        return False

    # Check if we should send notification based on preferences
    preferences = config['email']['notifications'].get('preferences', {})
    if (action == 'added' and not preferences.get('notify_added_items')) or \
       (action == 'removed' and not preferences.get('notify_removed_items')):
        return True

    # Create message
    msg = MIMEMultipart()
    msg['From'] = config['email']['sender']
    msg['To'] = recipient_email
    msg['Subject'] = f"Matförvaring - Vara {action}"

    # Create email body
    action_text = "tillagd" if action == "added" else "borttagen"
    emoji = "➕" if action == "added" else "➖"
    
    # Get expiration date with fallback
    expiration_date = item_details.get('expiration_date', None)
    if not expiration_date:
        expiration_date = 'Inget angivet'
    
    body = f"""
    <html>
    <body>
    <h2>{emoji} Vara {action_text}</h2>
    <ul>
        <li><strong>Vara:</strong> {item_details['item']}</li>
        <li><strong>Kategori:</strong> {item_details['category']}</li>
        <li><strong>Antal:</strong> {item_details['quantity']}</li>
        <li><strong>Förvaringsplats:</strong> {item_details['storage_unit']}</li>
        <li><strong>Utgångsdatum:</strong> {expiration_date}</li>
        <li><strong>Användare:</strong> {item_details.get('username', 'Okänd')}</li>
        <li><strong>Tidpunkt:</strong> {item_details['timestamp']}</li>
    </ul>
    <p>Med vänliga hälsningar,<br>Din Matförvaringsapp</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        # Create secure SSL/TLS connection
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(config['email']['sender'], config['email']['app_password'])
        
        # Send email
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def send_user_management_notification(action, username, performed_by=None):
    """Send notification about user management actions"""
    config = load_email_config()
    if not config:
        st.error("Kunde inte ladda email-konfiguration")
        return False

    recipient_email = st.secrets["email"]["recipient"]

    # Create message
    msg = MIMEMultipart()
    msg['From'] = config['email']['sender']
    msg['To'] = recipient_email
    msg['Subject'] = "Matförvaring - Användarhantering"

    # Create action-specific message
    if action == "created":
        title = "Ny användare skapad"
        details = f"En ny användare '{username}' har skapats"
    elif action == "deleted":
        title = "Användare borttagen"
        details = f"Användaren '{username}' har tagits bort"
    elif action == "password_changed":
        title = "Lösenord ändrat"
        details = f"Lösenordet har ändrats för användaren '{username}'"

    if performed_by:
        details += f" av {performed_by}"

    # Create email body
    body = f"""
    <html>
    <body>
    <h2>Matförvaring - {title}</h2>
    <p>{details}</p>
    <p>Tidpunkt: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p>Med vänliga hälsningar,<br>Din Matförvaringsapp</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(config['email']['sender'], config['email']['app_password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False