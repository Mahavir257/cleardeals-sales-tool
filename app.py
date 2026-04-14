import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="CLEARDEALS Sales Control", layout="wide")

st.title("🚀 CLEARDEALS Sales Control System")

uploaded_file = st.file_uploader("Upload 'Meeting Date Report' CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # --- 1. SMART DATE CONVERSION ---
    # Your CSV uses DD/MM/YYYY. This line forces Python to understand that.
    df['Meeting-Date'] = pd.to_datetime(df['Meeting-Date'], format='%d/%m/%Y', errors='coerce')
    
    # Drop rows where date failed to parse (prevents the "blank" dashboard)
    df = df.dropna(subset=['Meeting-Date'])

    # --- 2. LOGIC FOR DEALS & MEETINGS ---
    df['is_deal'] = df['Feedbacks'].str.contains('Deal Closed', case=False, na=False)
    df['is_meeting_done'] = df['Contact Type'].str.contains('Meeting Done', case=False, na=False)

    # --- 3. SIDEBAR ---
    st.sidebar.header("🛠 Control Panel")
    
    all_assignees = sorted(df['Assignee'].dropna().unique().tolist())
    selected_assignees = st.sidebar.multiselect("Select Members", options=all_assignees, default=all_assignees)
    
    # Date Range with safety check
    min_date = df['Meeting-Date'].min().to_pydatetime()
    max_date = df['Meeting-Date'].max().to_pydatetime()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

    # --- 4. FILTERING ---
    mask = (df['Assignee'].isin(selected_assignees))
    if len(date_range) == 2:
        mask = mask & (df['Meeting-Date'].dt.date >= date_range[0]) & (df['Meeting-Date'].dt.date <= date_range[1])
    
    filtered_df = df[mask]

    # --- 5. THE "NOTHING SHOWING" FIX ---
    if filtered_df.empty:
        st.error("⚠️ No data found for the selected Date Range or Assignees. Try expanding your date filter in the sidebar!")
        st.write("Current Filter Start:", date_range[0])
        st.write("Data Available From:", min_date)
    else:
        # METRICS
        total_meetings = filtered_df['is_meeting_done'].sum()
        total_deals = filtered_df['is_deal'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Meetings Done", total_meetings)
        m2.metric("Deals Closed", total_deals)
        m3.metric("Conversion Rate", f"{(total_deals/total_meetings*100):.1f}%" if total_meetings > 0 else "0%")

        # CHARTS
        st.subheader("Performance Overview")
        fig = px.bar(filtered_df.groupby('Assignee')['is_meeting_done'].sum().reset_index(), 
                     x='Assignee', y='is_meeting_done', color_discrete_sequence=['#007bff'])
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Current Data View")
        st.dataframe(filtered_df[['Meeting-Date', 'Assignee', 'Name', 'Contact Type', 'Feedbacks']])

else:
    st.info("Please upload your CSV file to view the dashboard.")
