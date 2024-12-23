"""
Helper functions used across the application
"""

from datetime import datetime, timedelta

def strip_emoji(text):
    """Remove emoji and extra spaces from text
    
    Args:
        text (str): Text to clean, e.g. "🥛 Mejeri"
    
    Returns:
        str: Cleaned text, e.g. "Mejeri"
    """
    return ' '.join(text.split()[1:]) if text.split() else text

def format_date(date_obj):
    """Format date object to string
    
    Args:
        date_obj (datetime.date): Date to format
    
    Returns:
        str: Formatted date string (YYYY-MM-DD)
    """
    return date_obj.strftime("%Y-%m-%d")

def parse_date(date_str):
    """Parse date string to datetime object
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
    
    Returns:
        datetime.date: Parsed date object
    """
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def days_until(date_str):
    """Calculate days until given date
    
    Args:
        date_str (str): Target date in YYYY-MM-DD format
    
    Returns:
        int: Number of days until target date
    """
    target_date = parse_date(date_str)
    return (target_date - datetime.now().date()).days 