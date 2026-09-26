"""
app.py
------
The main PharmaGuard website, built with Streamlit.

How to run:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from analysis import (
    load_data,
    process_dataframe,
    get_dashboard_summary,
    get_category_summary,
)

st.set_page_config(page_title="PharmaGuard", page_icon="💊", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #10312B;
    margin-bottom: 0;
}
.subtitle {
    color: #6b7280;
    font-size: 0.95rem;
    margin-top: 2px;
    margin-bottom: 1.5rem;
}

.metric-card {
    padding: 20px 18px;
    border-radius: 12px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-value {
    font-size: 1.9rem;
    font-weight: 800;
    margin: 0;
    color: #10312B;
}
.metric-label {
    font-size: 0.82rem;
    color: #6b7280;
    margin: 2px 0 0 0;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.metric-accent {
    height: 4px;
    width: 36px;
    border-radius: 2px;
    margin-bottom: 10px;
}

.status-pill {
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    display: inline-block;
}
.pill-expired { background-color: #fde2e2; color: #b91c1c; }
.pill-soon { background-color: #fef3c7; color: #92400e; }
.pill-safe { background-color: #d1fae5; color: #047857; }

section[data-testid="stSidebar"] {
    background-color: #10312B;
}
section[data-testid="stSidebar"] * {
    color: #f0f4f2 !important;
}
section[data-testid="stSidebar"] .pill-expired { color: #b91c1c !important; }
section[data-testid="stSidebar"] .pill-soon { color: #92400e !important; }
section[data-testid="stSidebar"] .pill-safe { color: #047857 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">💊 PharmaGuard</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Pharmacy Inventory & Expiry Analyzer</p>', unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### PharmaGuard")
    uploaded_file = st.file_uploader("Upload inventory CSV", type=["csv"])
    st.divider()
    st.markdown("**Status Legend**")
    st.markdown(
        '<span class="status-pill" style="background-color:#fde2e2 !important; '
        'color:#b91c1c !important;">Expired</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<span class="status-pill" style="background-color:#fef3c7 !important; '
        'color:#92400e !important;">Expiring Soon</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<span class="status-pill" style="background-color:#d1fae5 !important; '
        'color:#047857 !important;">Safe</span>',
        unsafe_allow_html=True,
    )

if uploaded_file is None:
    st.info("Upload a CSV file from the sidebar to get started.")
    st.stop()

# ---------- Process Data ----------
raw_df = load_data(uploaded_file)
df = process_dataframe(raw_df)
summary = get_dashboard_summary(df)

# ---------- Metric Cards ----------
cards = [
    ("Total Medicines", summary["total_medicines"], "#2563eb"),
    ("Total Stock", summary["total_stock"], "#059669"),
    ("Inventory Value", f"${summary['total_inventory_value']:,.2f}", "#7c3aed"),
    ("Expired", summary["expired_count"], "#dc2626"),
    ("Expiring Soon", summary["expiring_soon_count"], "#d97706"),
]

cols = st.columns(5)
for col, (label, value, color) in zip(cols, cards):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-accent" style="background-color:{color};"></div>
            <p class="metric-value">{value}</p>
            <p class="metric-label">{label}</p>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# ---------- Tabs ----------
tab1, tab2, tab3, tab4 = st.tabs(["Inventory", "Expiry", "Analytics", "Charts"])

# --- Tab 1: Inventory Table ---
with tab1:
    categories = ["All"] + sorted(df["Category"].unique().tolist())
    selected_category = st.selectbox("Category", categories, label_visibility="collapsed")

    filtered_df = df if selected_category == "All" else df[df["Category"] == selected_category]

    st.dataframe(
        filtered_df[["Medicine_Name", "Category", "Quantity", "Price", "Expiry_Date"]],
        use_container_width=True,
        hide_index=True,
    )

    st.write("")
    category_summary = get_category_summary(df)
    st.dataframe(category_summary, use_container_width=True, hide_index=True)

# --- Tab 2: Expiry ---
with tab2:
    def status_pill(status):
        css_class = {"Expired": "pill-expired", "Expiring Soon": "pill-soon", "Safe": "pill-safe"}[status]
        return f'<span class="status-pill {css_class}">{status}</span>'

    display_df = df[["Medicine_Name", "Expiry_Date", "Days_Remaining", "Expiry_Status"]].copy()
    display_df["Expiry_Date"] = display_df["Expiry_Date"].dt.strftime("%Y-%m-%d")
    display_df["Status"] = display_df["Expiry_Status"].apply(status_pill)
    display_df = display_df.drop(columns=["Expiry_Status"])

    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

# --- Tab 3: Analytics ---
with tab3:
    inv_df = df[[
        "Medicine_Name", "Quantity", "Price", "Daily_Sales",
        "Estimated_Sales_Before_Expiry", "Potential_Expired_Quantity"
    ]]
    st.dataframe(inv_df, use_container_width=True, hide_index=True)

# --- Tab 4: Charts ---
with tab4:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        cat_counts = df["Category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig1 = px.pie(cat_counts, names="Category", values="Count", hole=0.55,
                      color_discrete_sequence=px.colors.sequential.Teal)
        fig1.update_layout(title="Medicines by Category", margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col2:
        status_counts = df["Expiry_Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        color_map = {"Expired": "#dc2626", "Expiring Soon": "#d97706", "Safe": "#059669"}
        fig2 = px.pie(status_counts, names="Status", values="Count", hole=0.55,
                      color="Status", color_discrete_map=color_map)
        fig2.update_layout(title="Expiry Status", margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)

    stock_df = df[["Medicine_Name", "Quantity"]].sort_values("Quantity", ascending=False)
    fig3 = px.bar(stock_df, x="Medicine_Name", y="Quantity",
                  color="Quantity", color_continuous_scale="Teal")
    fig3.update_layout(title="Stock Quantity by Medicine", xaxis_tickangle=-40,
                        margin=dict(t=50, b=10, l=10, r=10))
    st.plotly_chart(fig3, use_container_width=True)