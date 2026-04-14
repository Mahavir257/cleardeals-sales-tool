import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re

st.set_page_config(page_title="Sales Master Dashboard", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #e0e0e0; }
    .main { background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Sales Master Dashboard")

# --- DATA INPUT ---
st.sidebar.header("📥 Data Source")
input_method = st.sidebar.radio("Input Method", ["File Upload", "Google Sheet Link"])

df = None
if input_method == "File Upload":
    file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if file:
        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
else:
    url = st.sidebar.text_input("Paste Google Sheet Link:")
    if url:
        try:
            sheet_id = re.search(r'd/([a-zA-Z0-9-_]+)', url).group(1)
            df = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv")
        except: st.sidebar.error("Invalid Link")

if df is not None:
    # --- DATA PREP ---
    df['Meeting-Date'] = pd.to_datetime(df['Meeting-Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Meeting-Date'])
    df['is_deal'] = df['Feedbacks'].str.contains('Deal Closed', case=False, na=False).astype(int)
    df['is_meeting'] = df['Contact Type'].str.contains('Meeting Done', case=False, na=False).astype(int)

    # --- NAVIGATION TABS ---
    tab1, tab2, tab3 = st.tabs(["📈 Main Dashboard", "⚔️ BDE Comparison", "📅 Calendar View"])

    # --- TAB 1: MAIN DASHBOARD ---
    with tab1:
        st.sidebar.divider()
        all_bdes = sorted(df['Assignee'].dropna().unique().tolist())
        selected = st.sidebar.multiselect("Filter Team", all_bdes, default=all_bdes)
        f_df = df[df['Assignee'].isin(selected)]

        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Meetings", f_df['is_meeting'].sum())
        c2.metric("Deals Closed", f_df['is_deal'].sum())
        c3.metric("Conv. Rate", f"{(f_df['is_deal'].sum()/f_df['is_meeting'].sum()*100):.1f}%" if f_df['is_meeting'].sum()>0 else "0%")

        # View Selector
        view = st.radio("Chart View", ["Bar Chart (Performance)", "Trend Line (Timeline)"], horizontal=True)
        if view == "Bar Chart (Performance)":
            fig = px.bar(f_df.groupby('Assignee')['is_meeting'].sum().reset_index(), x='Assignee', y='is_meeting', color='is_meeting')
        else:
            fig = px.line(f_df.groupby('Meeting-Date')['is_meeting'].sum().reset_index(), x='Meeting-Date', y='is_meeting', markers=True)
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: BDE COMPARISON ---
    with tab2:
        st.subheader("Compare Performance (BDE vs BDE)")
        col_x, col_y = st.columns(2)
        bde_1 = col_x.selectbox("Select BDE 1", all_bdes, index=0)
        bde_2 = col_y.selectbox("Select BDE 2", all_bdes, index=1 if len(all_bdes)>1 else 0)

        comp_df = df[df['Assignee'].isin([bde_1, bde_2])]
        comp_stats = comp_df.groupby('Assignee').agg({'is_meeting':'sum', 'is_deal':'sum', 'Name':'count'})
        st.bar_chart(comp_stats[['is_meeting', 'is_deal']])
        st.table(comp_stats)

    # --- TAB 3: CALENDAR VIEW ---
    with tab3:
        st.subheader("Meeting Density Calendar")
        # Create a heatmap-style view
        cal_df = f_df.groupby('Meeting-Date').size().reset_index(name='Meetings')
        fig_cal = px.scatter(cal_df, x='Meeting-Date', y='Meetings', size='Meetings', color='Meetings', title="Daily Meeting Volume")
        st.plotly_chart(fig_cal, use_container_width=True)
        
        st.write("### Raw Data Log")
        st.dataframe(f_df[['Meeting-Date', 'Assignee', 'Name', 'Contact Type', 'Feedbacks']], use_container_width=True)

    # --- DOWNLOAD ---
    csv = f_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download Master Report", data=csv, file_name="Sales_Master_Report.csv")

else:
    st.info("Please upload data to activate the Sales Master Dashboard.")
