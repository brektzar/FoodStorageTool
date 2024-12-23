"""
Statistics view UI component
"""

import streamlit as st
from utils.stats import generate_activity_stats, create_activity_charts
from models.history import HistoryManager

def render_statistics_view():
    """Render the statistics view"""
    st.title("📊 Statistik och Analys")
    
    history_mgr = HistoryManager()
    
    if not st.session_state.item_history:
        st.info("Ingen historik tillgänglig än. Börja med att lägga till och ta bort varor!")
        return

    # Time period selector
    time_period = st.selectbox(
        "Välj tidsperiod",
        ["Senaste veckan", "Senaste månaden", "Senaste året", "Allt"]
    )

    if st.button("Visa statistik", type="primary"):
        with st.spinner("Genererar statistik..."):
            # Get statistics data
            time_filter = None if time_period == "Allt" else time_period.lower().split()[-1]
            df, category_stats, item_stats = generate_activity_stats(
                st.session_state.item_history,
                time_filter
            )

            if df is not None:
                render_activity_statistics(df, category_stats, item_stats)
                render_expiration_statistics(df)
                render_summary_metrics(df)

def render_activity_statistics(df, category_stats, item_stats):
    """Render activity statistics section"""
    with st.expander("Aktivitetsstatistik", expanded=True):
        st.write("### Aktivitetsstatistik")
        
        # Get charts
        charts = create_activity_charts(df, category_stats, item_stats)
        
        # Display charts
        st.plotly_chart(charts['category_pie'], use_container_width=True)
        
        if 'most_added' in charts:
            st.plotly_chart(charts['most_added'], use_container_width=True)
            
        st.plotly_chart(charts['daily_activity'], use_container_width=True)

def render_expiration_statistics(df):
    """Render expiration statistics section"""
    with st.expander("Utgångsstatistik"):
        st.write("### 📅 Statistik över utgångna varor")
        
        # Filter expired items
        expired_df = df[df['expired'] == True]
        
        if not expired_df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Totalt antal utgångna varor",
                    len(expired_df)
                )
            
            with col2:
                avg_lifetime = (
                    expired_df['expiration_date'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d")) - 
                    expired_df['timestamp']
                ).mean().days
                st.metric(
                    "Genomsnittlig livstid",
                    f"{avg_lifetime:.1f} dagar"
                )
            
            with col3:
                most_expired_category = expired_df['category'].mode().iloc[0]
                st.metric(
                    "Vanligaste utgångna kategori",
                    most_expired_category
                )
        else:
            st.info("Ingen data om utgångna varor tillgänglig")

def render_summary_metrics(df):
    """Render summary metrics"""
    with st.expander("Sammanfattande statistik"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_items = len(df[df['action'] == 'added'])
            st.metric(
                "Totalt antal tillagda varor",
                total_items
            )
        
        with col2:
            used_items = len(df[
                (df['action'] == 'removed') &
                (df['expired'] == False)
            ])
            st.metric(
                "Använda varor (ej utgångna)",
                used_items
            )
        
        with col3:
            expired_items = len(df[
                (df['action'] == 'removed') &
                (df['expired'] == True)
            ])
            st.metric(
                "Utgångna varor",
                expired_items
            ) 