import os
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

st.set_page_config(page_title="Campora AI Dashboard", page_icon="📊", layout="wide")


@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


@st.cache_data(ttl=300)
def fetch_interactions() -> pd.DataFrame:
    supabase = get_supabase_client()

    columns = (
        "id, user_id, username, chat_id, chat_type, input_message, command_used, "
        "search_results_count, response_time_ms, status, ai_model_used, tokens_used, "
        "user_language, user_feedback, created_at"
    )

    all_rows = []
    page_size = 1000
    offset = 0

    while True:
        result = supabase.table("bot_interactions").select(columns).range(offset, offset + page_size - 1).execute()
        rows = result.data or []
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        offset += page_size

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    return df


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

raw_df = fetch_interactions()

if raw_df.empty:
    st.title("Campora AI Dashboard")
    st.warning("No interaction data found. Make sure the bot has logged some interactions first.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.title("Filters")

min_date = raw_df["date"].min()
max_date = raw_df["date"].max()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

commands = ["All"] + sorted(raw_df["command_used"].dropna().unique().tolist())
selected_command = st.sidebar.selectbox("Command", commands)

statuses = ["All"] + sorted(raw_df["status"].dropna().unique().tolist())
selected_status = st.sidebar.selectbox("Status", statuses)

languages = ["All"] + sorted(raw_df["user_language"].dropna().unique().tolist())
selected_language = st.sidebar.selectbox("Language", languages)

if st.sidebar.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

# Apply filters
df = raw_df[(raw_df["date"] >= start_date) & (raw_df["date"] <= end_date)].copy()

if selected_command != "All":
    df = df[df["command_used"] == selected_command]
if selected_status != "All":
    df = df[df["status"] == selected_status]
if selected_language != "All":
    df = df[df["user_language"] == selected_language]

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------

st.title("Campora AI Dashboard")
st.caption(f"Showing **{len(df)}** interactions from **{start_date}** to **{end_date}**")

# ---------------------------------------------------------------------------
# KPI Summary
# ---------------------------------------------------------------------------

total = len(df)
feedback_given = df["user_feedback"].notna().sum()
feedback_rate = (feedback_given / total * 100) if total else 0
likes = (df["user_feedback"] == "like").sum()
like_ratio = (likes / feedback_given * 100) if feedback_given else 0
avg_latency = df["response_time_ms"].dropna().mean()
avg_latency = avg_latency if pd.notna(avg_latency) else 0
errors = (df["status"] == "error").sum()
error_rate = (errors / total * 100) if total else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Interactions", f"{total:,}")
k2.metric("Feedback Rate", f"{feedback_rate:.1f}%")
k3.metric("Like Ratio", f"{like_ratio:.1f}%")
k4.metric("Avg Latency", f"{avg_latency:,.0f} ms")
k5.metric("Error Rate", f"{error_rate:.1f}%")

st.divider()

# ---------------------------------------------------------------------------
# Popular Queries
# ---------------------------------------------------------------------------

st.header("Popular Queries")

query_counts = df["input_message"].value_counts().head(20).reset_index()
query_counts.columns = ["Query", "Count"]

col_table, col_chart = st.columns([1, 1])

with col_table:
    st.dataframe(query_counts, use_container_width=True, hide_index=True, height=400)

with col_chart:
    top_10 = query_counts.head(10)
    fig = px.bar(
        top_10,
        x="Count",
        y="Query",
        orientation="h",
        title="Top 10 Queries",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"), height=400, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Response Quality (Feedback)
# ---------------------------------------------------------------------------

st.header("Response Quality")

col_donut, col_trend = st.columns([1, 1])

with col_donut:
    feedback_dist = pd.DataFrame(
        {
            "Feedback": ["Like", "Dislike", "No feedback"],
            "Count": [
                (df["user_feedback"] == "like").sum(),
                (df["user_feedback"] == "dislike").sum(),
                df["user_feedback"].isna().sum(),
            ],
        }
    )
    fig = px.pie(
        feedback_dist,
        values="Count",
        names="Feedback",
        hole=0.45,
        title="Feedback Distribution",
        color="Feedback",
        color_discrete_map={"Like": "#2ecc71", "Dislike": "#e74c3c", "No feedback": "#95a5a6"},
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col_trend:
    feedback_only = df[df["user_feedback"].notna()].copy()
    if not feedback_only.empty:
        daily_fb = feedback_only.groupby(["date", "user_feedback"]).size().reset_index(name="count")
        fig = px.line(
            daily_fb,
            x="date",
            y="count",
            color="user_feedback",
            title="Feedback Trend Over Time",
            color_discrete_map={"like": "#2ecc71", "dislike": "#e74c3c"},
            markers=True,
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No feedback data yet.")

fb_by_cmd, fb_by_lang = st.columns(2)

with fb_by_cmd:
    fb_cmd = df[df["user_feedback"].notna()].groupby(["command_used", "user_feedback"]).size().reset_index(name="count")
    if not fb_cmd.empty:
        fig = px.bar(fb_cmd, x="command_used", y="count", color="user_feedback", barmode="group", title="Feedback by Command", color_discrete_map={"like": "#2ecc71", "dislike": "#e74c3c"})
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

with fb_by_lang:
    fb_lang = df[df["user_feedback"].notna()].groupby(["user_language", "user_feedback"]).size().reset_index(name="count")
    if not fb_lang.empty:
        fig = px.bar(fb_lang, x="user_language", y="count", color="user_feedback", barmode="group", title="Feedback by Language", color_discrete_map={"like": "#2ecc71", "dislike": "#e74c3c"})
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Latency Trends
# ---------------------------------------------------------------------------

st.header("Latency Trends")

latency_data = df[df["response_time_ms"].notna()].copy()

if not latency_data.empty:
    p50 = latency_data["response_time_ms"].quantile(0.50)
    p95 = latency_data["response_time_ms"].quantile(0.95)
    p99 = latency_data["response_time_ms"].quantile(0.99)

    lk1, lk2, lk3 = st.columns(3)
    lk1.metric("P50 Latency", f"{p50:,.0f} ms")
    lk2.metric("P95 Latency", f"{p95:,.0f} ms")
    lk3.metric("P99 Latency", f"{p99:,.0f} ms")

    col_ts, col_hist = st.columns([1, 1])

    with col_ts:
        daily_latency = latency_data.groupby("date")["response_time_ms"].mean().reset_index()
        daily_latency.columns = ["Date", "Avg Response Time (ms)"]
        fig = px.line(
            daily_latency,
            x="Date",
            y="Avg Response Time (ms)",
            title="Average Response Time Per Day",
            markers=True,
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_hist:
        fig = px.histogram(
            latency_data,
            x="response_time_ms",
            nbins=40,
            title="Response Time Distribution",
            labels={"response_time_ms": "Response Time (ms)"},
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No latency data available.")

st.divider()

# ---------------------------------------------------------------------------
# Search Hit Rates
# ---------------------------------------------------------------------------

st.header("Search Hit Rates")

search_data = df[df["search_results_count"].notna()].copy()

if not search_data.empty:
    no_results_count = (df["status"] == "no_results").sum()
    no_results_pct = (no_results_count / total * 100) if total else 0
    avg_results = search_data["search_results_count"].mean()

    sk1, sk2, sk3 = st.columns(3)
    sk1.metric("Avg Results Per Query", f"{avg_results:.1f}")
    sk2.metric("Zero-Result Queries", f"{no_results_count:,}")
    sk3.metric("Zero-Result Rate", f"{no_results_pct:.1f}%")

    col_dist, col_trend = st.columns([1, 1])

    with col_dist:
        fig = px.histogram(
            search_data,
            x="search_results_count",
            nbins=max(int(search_data["search_results_count"].max()), 10),
            title="Search Results Count Distribution",
            labels={"search_results_count": "Number of Results"},
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_trend:
        daily_no_results = df.groupby("date").apply(lambda g: (g["status"] == "no_results").sum()).reset_index(name="No Results")
        daily_total = df.groupby("date").size().reset_index(name="Total")
        daily_merged = daily_no_results.merge(daily_total, on="date")
        daily_merged["No-Result Rate (%)"] = daily_merged["No Results"] / daily_merged["Total"] * 100
        fig = px.line(
            daily_merged,
            x="date",
            y="No-Result Rate (%)",
            title="Zero-Result Rate Over Time",
            markers=True,
        )
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No search data available.")

st.divider()

# ---------------------------------------------------------------------------
# Usage Patterns
# ---------------------------------------------------------------------------

st.header("Usage Patterns")

col_daily, col_users = st.columns([1, 1])

with col_daily:
    daily_interactions = df.groupby("date").size().reset_index(name="Interactions")
    fig = px.bar(
        daily_interactions,
        x="date",
        y="Interactions",
        title="Interactions Per Day",
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col_users:
    daily_users = df.groupby("date")["user_id"].nunique().reset_index(name="Unique Users")
    fig = px.line(
        daily_users,
        x="date",
        y="Unique Users",
        title="Active Users Per Day",
        markers=True,
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

col_chat, col_lang = st.columns([1, 1])

with col_chat:
    chat_type_dist = df["chat_type"].value_counts().reset_index()
    chat_type_dist.columns = ["Chat Type", "Count"]
    fig = px.pie(
        chat_type_dist,
        values="Count",
        names="Chat Type",
        title="Chat Type Distribution",
        hole=0.4,
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col_lang:
    lang_dist = df["user_language"].value_counts().reset_index()
    lang_dist.columns = ["Language", "Count"]
    fig = px.pie(
        lang_dist,
        values="Count",
        names="Language",
        title="Language Distribution",
        hole=0.4,
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)
