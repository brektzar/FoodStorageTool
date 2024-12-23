"""
Statistics calculation and analysis utilities
"""

import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.helpers import strip_emoji

def generate_activity_stats(history_data, time_filter=None):
    """Generate activity statistics from history data
    
    Args:
        history_data (list): List of history entries
        time_filter (str): Optional time filter ('week', 'month', 'year')
    
    Returns:
        tuple: (activity_df, category_stats, item_stats)
    """
    if not history_data:
        return None, None, None

    # Convert to DataFrame
    df = pd.DataFrame(history_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Apply time filter
    if time_filter:
        now = pd.Timestamp.now()
        if time_filter == 'week':
            df = df[df['timestamp'] > now - pd.Timedelta(days=7)]
        elif time_filter == 'month':
            df = df[df['timestamp'] > now - pd.Timedelta(days=30)]
        elif time_filter == 'year':
            df = df[df['timestamp'] > now - pd.Timedelta(days=365)]

    # Category statistics
    category_stats = df['category'].value_counts()

    # Item statistics
    item_stats = {
        'most_added': df[df['action'] == 'added']['item'].value_counts().head(10),
        'most_used': df[
            (df['action'] == 'removed') & 
            (df['expired'] == False)
        ]['item'].value_counts().head(10),
        'most_expired': df[
            (df['action'] == 'removed') & 
            (df['expired'] == True)
        ]['item'].value_counts().head(10)
    }

    return df, category_stats, item_stats

def create_activity_charts(df, category_stats, item_stats):
    """Create plotly charts for activity statistics
    
    Args:
        df (DataFrame): Activity DataFrame
        category_stats (Series): Category statistics
        item_stats (dict): Item statistics
    
    Returns:
        dict: Dictionary of plotly figures
    """
    charts = {}
    
    # Category pie chart
    charts['category_pie'] = px.pie(
        values=category_stats.values,
        names=category_stats.index,
        title="Aktivitet per kategori"
    )

    # Most added items bar chart
    if not item_stats['most_added'].empty:
        charts['most_added'] = px.bar(
            data_frame=pd.DataFrame({
                'Vara': item_stats['most_added'].index,
                'Antal': item_stats['most_added'].values
            }),
            x='Vara',
            y='Antal',
            title="Topp 10 tillagda varor"
        )

    # Daily activity chart
    daily_activity = df.groupby(df['timestamp'].dt.date).size().reset_index()
    daily_activity.columns = ['Datum', 'Antal']
    charts['daily_activity'] = px.bar(
        daily_activity,
        x='Datum',
        y='Antal',
        title="Daglig aktivitet"
    )

    return charts 