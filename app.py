import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Cloud Kitchen PNL Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    file_path = "Kittchen PNL Data.xlsx"

    raw_df = pd.read_excel(file_path)

    # First row as header
    raw_df.columns = raw_df.iloc[0]

    # Remove first row
    df = raw_df[1:].copy()

    # Reset index
    df.reset_index(drop=True, inplace=True)

    # Clean column names
    df.columns = [str(col).strip().replace(" ", "_") for col in df.columns]

    # Numeric columns
    numeric_cols = [
        'ORDER_COUNT',
        'CART_SALES',
        'DISCOUNT',
        'NET_REVENUE',
        'IDEAL_FOOD_COST',
        'GROSS_MARGIN',
        'KITCHEN_EBITDA',
        'VARIANCE'
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Date column
    df['MONTH'] = pd.to_datetime(df['MONTH'], format='%b-%Y')

    # Month string
    df['MONTH_STR'] = df['MONTH'].dt.strftime('%b-%Y')

    # Metrics
    df['GM_PERCENT'] = (
        df['GROSS_MARGIN'] / df['NET_REVENUE']
    ) * 100

    df['CM'] = df['GROSS_MARGIN'] - df['VARIANCE']

    df['CM_PERCENT'] = (
        df['CM'] / df['NET_REVENUE']
    ) * 100

    df['EBITDA_PERCENT'] = (
        df['KITCHEN_EBITDA'] / df['NET_REVENUE']
    ) * 100

    df['VARIANCE_PERCENT'] = (
        df['VARIANCE'] / df['NET_REVENUE']
    ) * 100

    return df


# ============================================================
# LOAD DATAFRAME
# ============================================================

df = load_data()

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Filters")

selected_store = st.sidebar.multiselect(
    "Store",
    options=sorted(df['STORE'].dropna().unique()),
    default=sorted(df['STORE'].dropna().unique())
)

selected_city = st.sidebar.multiselect(
    "City",
    options=sorted(df['CITY'].dropna().unique()),
    default=sorted(df['CITY'].dropna().unique())
)

selected_month = st.sidebar.multiselect(
    "Month",
    options=sorted(df['MONTH_STR'].dropna().unique()),
    default=sorted(df['MONTH_STR'].dropna().unique())
)

# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df[
    (df['STORE'].isin(selected_store)) &
    (df['CITY'].isin(selected_city)) &
    (df['MONTH_STR'].isin(selected_month))
]

# ============================================================
# TITLE
# ============================================================

st.title("📊 Cloud Kitchen PNL Dashboard")

# ============================================================
# KPI SECTION
# ============================================================

st.header("Kitchen Level PNL")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Net Revenue",
        f"₹ {filtered_df['NET_REVENUE'].sum():,.0f}"
    )

with col2:
    st.metric(
        "Gross Margin",
        f"₹ {filtered_df['GROSS_MARGIN'].sum():,.0f}"
    )

with col3:
    st.metric(
        "EBITDA",
        f"₹ {filtered_df['KITCHEN_EBITDA'].sum():,.0f}"
    )

with col4:
    st.metric(
        "Variance",
        f"₹ {filtered_df['VARIANCE'].sum():,.0f}"
    )

st.markdown("---")

# ============================================================
# MONTHLY REVENUE TREND
# ============================================================

monthly_revenue = filtered_df.groupby(
    'MONTH_STR',
    as_index=False
)['NET_REVENUE'].sum()

fig_revenue = px.line(
    monthly_revenue,
    x='MONTH_STR',
    y='NET_REVENUE',
    title='Monthly Revenue Trend',
    markers=True
)

st.plotly_chart(fig_revenue, use_container_width=True)

# ============================================================
# CITY PERFORMANCE
# ============================================================

city_summary = filtered_df.groupby(
    'CITY',
    as_index=False
).agg({
    'NET_REVENUE': 'sum',
    'KITCHEN_EBITDA': 'sum'
})

fig_city = px.bar(
    city_summary,
    x='CITY',
    y='NET_REVENUE',
    color='KITCHEN_EBITDA',
    title='City-wise Revenue & EBITDA'
)

st.plotly_chart(fig_city, use_container_width=True)

# ============================================================
# STORE PERFORMANCE TABLE
# ============================================================

store_summary = filtered_df.groupby(
    'STORE',
    as_index=False
).agg({
    'NET_REVENUE': 'sum',
    'GROSS_MARGIN': 'sum',
    'KITCHEN_EBITDA': 'sum',
    'VARIANCE': 'sum',
    'ORDER_COUNT': 'sum'
})

store_summary = store_summary.sort_values(
    by='NET_REVENUE',
    ascending=False
)

st.subheader("Store Performance Summary")

st.dataframe(store_summary, use_container_width=True)

# ============================================================
# TOP STORES
# ============================================================

fig_top_store = px.bar(
    store_summary.head(10),
    x='STORE',
    y='NET_REVENUE',
    title='Top 10 Stores by Revenue'
)

st.plotly_chart(fig_top_store, use_container_width=True)

# ============================================================
# EBITDA DISTRIBUTION
# ============================================================

fig_ebitda = px.histogram(
    filtered_df,
    x='EBITDA_PERCENT',
    nbins=30,
    title='EBITDA Percentage Distribution'
)

st.plotly_chart(fig_ebitda, use_container_width=True)

# ============================================================
# VARIANCE DASHBOARD
# ============================================================

st.markdown("---")
st.header("Variance Level PNL Dashboard")

# Variance buckets
variance_bins = [
    -100,
    0,
    1,
    2,
    3,
    5,
    100
]

variance_labels = [
    'Below 0%',
    '0% - 1%',
    '1% - 2%',
    '2% - 3%',
    '3% - 5%',
    'Above 5%'
]

filtered_df['VARIANCE_BUCKET'] = pd.cut(
    filtered_df['VARIANCE_PERCENT'],
    bins=variance_bins,
    labels=variance_labels
)

selected_variance = st.selectbox(
    "Select Variance Bucket",
    variance_labels
)

variance_filtered_df = filtered_df[
    filtered_df['VARIANCE_BUCKET'] == selected_variance
]

# ============================================================
# SUB DASHBOARD 1
# ============================================================

st.subheader("Average Variance % by Revenue Cohort")

variance_summary = variance_filtered_df.groupby(
    'REVENUE_COHORT',
    as_index=False
)['VARIANCE_PERCENT'].mean()

fig_variance = px.bar(
    variance_summary,
    x='REVENUE_COHORT',
    y='VARIANCE_PERCENT',
    title='Average Variance Percentage',
    text_auto=True
)

st.plotly_chart(fig_variance, use_container_width=True)

# ============================================================
# REVENUE BUCKETS
# ============================================================

revenue_bins = [
    0,
    1000000,
    2000000,
    3000000,
    4000000,
    5000000,
    np.inf
]

revenue_labels = [
    '0-10L',
    '10L-20L',
    '20L-30L',
    '30L-40L',
    '40L-50L',
    '50L+'
]

variance_filtered_df['REVENUE_BUCKET'] = pd.cut(
    variance_filtered_df['NET_REVENUE'],
    bins=revenue_bins,
    labels=revenue_labels
)

# ============================================================
# STORE COUNT MATRIX
# ============================================================

st.subheader("Store Count by Revenue Bucket & Month")

store_count_matrix = pd.pivot_table(
    variance_filtered_df,
    values='STORE',
    index='REVENUE_BUCKET',
    columns='MONTH_STR',
    aggfunc='count',
    fill_value=0
)

st.dataframe(store_count_matrix, use_container_width=True)

# ============================================================
# HEATMAP
# ============================================================

fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=store_count_matrix.values,
        x=store_count_matrix.columns,
        y=store_count_matrix.index,
        text=store_count_matrix.values,
        texttemplate="%{text}",
        colorscale='Viridis'
    )
)

fig_heatmap.update_layout(
    title='Store Count Heatmap'
)

st.plotly_chart(fig_heatmap, use_container_width=True)

# ============================================================
# EXTRA INSIGHTS
# ============================================================

st.markdown("---")
st.header("Additional Insights")

top_ebitda = filtered_df.groupby(
    'STORE',
    as_index=False
)['KITCHEN_EBITDA'].sum()

top_ebitda = top_ebitda.sort_values(
    by='KITCHEN_EBITDA',
    ascending=False
).head(5)

st.subheader("Top 5 EBITDA Stores")

st.dataframe(top_ebitda, use_container_width=True)

worst_variance = filtered_df.groupby(
    'STORE',
    as_index=False
)['VARIANCE_PERCENT'].mean()

worst_variance = worst_variance.sort_values(
    by='VARIANCE_PERCENT',
    ascending=False
).head(5)

st.subheader("Highest Variance % Stores")

st.dataframe(worst_variance, use_container_width=True)

# ============================================================
# DOWNLOAD BUTTON
# ============================================================

csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Filtered Data",
    data=csv,
    file_name='filtered_kitchen_pnl.csv',
    mime='text/csv'
)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption("Created using Streamlit + Plotly")