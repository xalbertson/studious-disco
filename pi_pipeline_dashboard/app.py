"""PI Pipeline Dashboard.

Run with: streamlit run app.py
"""

import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

from constants import (
    ASSET_CLASS_OPTIONS,
    CATEGORICAL_SEQUENCE,
    DATA_PATH,
    FUNDRAISING_STATUS_OPTIONS,
    GEOGRAPHY_OPTIONS,
    SEQUENTIAL_BLUE,
    SOURCE_OPTIONS,
    STAGE_COLOR_MAP,
    STAGE_OPTIONS,
    STAGE_RANK,
)
from data_utils import load_data, save_data, stage_sort_key

st.set_page_config(page_title="PI Pipeline Dashboard", layout="wide")

if "df" not in st.session_state:
    st.session_state.df = load_data()


def refresh():
    st.session_state.df = load_data()


st.title("PI Pipeline Dashboard")

tab_entry, tab_overview, tab_conviction, tab_geo, tab_asset, tab_fundraising = st.tabs(
    [
        "📋 Data Entry",
        "📊 Overview",
        "🎯 By Conviction",
        "🌍 By Geography",
        "🏢 By Asset Class",
        "📅 Fundraising Timeline",
    ]
)

# ---------------------------------------------------------------------------
# Data Entry
# ---------------------------------------------------------------------------
with tab_entry:
    st.caption(
        "Add or edit firms below. Click **Save changes** to persist to "
        f"`{DATA_PATH}`. Rows with a blank Firm are dropped on save."
    )

    edited = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        width='stretch',
        height=500,
        column_config={
            "Stage": st.column_config.SelectboxColumn("Stage (Conviction)", options=STAGE_OPTIONS),
            "Asset Class": st.column_config.SelectboxColumn(options=ASSET_CLASS_OPTIONS),
            "Geography": st.column_config.SelectboxColumn(options=GEOGRAPHY_OPTIONS),
            "Source": st.column_config.SelectboxColumn(options=SOURCE_OPTIONS),
            "Fundraising Status": st.column_config.SelectboxColumn(options=FUNDRAISING_STATUS_OPTIONS),
            "Client Invested": st.column_config.CheckboxColumn("Client Invested?"),
            "Target Close Date": st.column_config.DateColumn(),
            "Next Follow Up Date": st.column_config.DateColumn(),
            "Last Updated": st.column_config.DateColumn(),
            "Commentary": st.column_config.TextColumn(width="large"),
        },
        key="pipeline_editor",
    )

    col_save, col_reload, _ = st.columns([1, 1, 4])
    if col_save.button("💾 Save changes", type="primary"):
        edited["Last Updated"] = edited["Last Updated"].where(
            edited["Last Updated"].notna(), pd.Timestamp(dt.date.today())
        )
        save_data(edited)
        st.session_state.df = load_data()
        st.success(f"Saved {len(st.session_state.df)} firms.")
    if col_reload.button("↩️ Discard changes / reload"):
        refresh()
        st.rerun()

# ---------------------------------------------------------------------------
# Shared sidebar filters for exhibit tabs
# ---------------------------------------------------------------------------
df = st.session_state.df

st.sidebar.header("Filters")
st.sidebar.caption("Applies to the exhibit tabs (not Data Entry).")

f_stage = st.sidebar.multiselect("Stage / Conviction", STAGE_OPTIONS)
f_asset = st.sidebar.multiselect("Asset Class", ASSET_CLASS_OPTIONS)
f_geo = st.sidebar.multiselect("Geography", sorted([g for g in df["Geography"].unique() if g]))
f_fundraising = st.sidebar.multiselect("Fundraising Status", FUNDRAISING_STATUS_OPTIONS)
f_invested = st.sidebar.selectbox("Client Invested?", ["All", "Yes", "No"])
f_search = st.sidebar.text_input("Search firm / commentary")

filtered = df.copy()
if f_stage:
    filtered = filtered[filtered["Stage"].isin(f_stage)]
if f_asset:
    filtered = filtered[filtered["Asset Class"].isin(f_asset)]
if f_geo:
    filtered = filtered[filtered["Geography"].isin(f_geo)]
if f_fundraising:
    filtered = filtered[filtered["Fundraising Status"].isin(f_fundraising)]
if f_invested == "Yes":
    filtered = filtered[filtered["Client Invested"]]
elif f_invested == "No":
    filtered = filtered[~filtered["Client Invested"]]
if f_search:
    needle = f_search.lower()
    filtered = filtered[
        filtered["Firm"].str.lower().str.contains(needle)
        | filtered["Commentary"].str.lower().str.contains(needle)
    ]

st.sidebar.caption(f"{len(filtered)} of {len(df)} firms shown")

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Firms in view", len(filtered))
    c2.metric("Top conviction (Stage 1)", int((stage_sort_key(filtered) == 1).sum()))
    c3.metric("Client invested", int(filtered["Client Invested"].sum()))
    c4.metric(
        "Currently raising",
        int(filtered["Fundraising Status"].isin(
            ["Raising - Early Stage", "Raising - Final Close"]
        ).sum()),
    )

    st.subheader("All firms")
    st.dataframe(
        filtered.sort_values(by=["Firm"]).reset_index(drop=True),
        width='stretch',
        height=500,
    )

# ---------------------------------------------------------------------------
# By Conviction
# ---------------------------------------------------------------------------
with tab_conviction:
    st.subheader("Pipeline by conviction (Stage)")

    counts = (
        filtered[filtered["Stage"] != ""]
        .groupby(["Stage", "Asset Class"])
        .size()
        .reset_index(name="Count")
    )
    if counts.empty:
        st.info("No rows match the current filters.")
    else:
        fig = px.bar(
            counts,
            x="Stage",
            y="Count",
            color="Asset Class",
            category_orders={"Stage": STAGE_OPTIONS, "Asset Class": ASSET_CLASS_OPTIONS},
            color_discrete_sequence=CATEGORICAL_SEQUENCE,
        )
        fig.update_layout(legend_title_text="Asset Class", xaxis_title=None, yaxis_title="Firms")
        st.plotly_chart(fig, width='stretch')

    st.subheader("Firms sorted by conviction")
    sorted_df = filtered.assign(_rank=stage_sort_key(filtered)).sort_values(
        by=["_rank", "Firm"]
    ).drop(columns="_rank")
    st.dataframe(sorted_df.reset_index(drop=True), width='stretch', height=450)

# ---------------------------------------------------------------------------
# By Geography
# ---------------------------------------------------------------------------
with tab_geo:
    st.subheader("Pipeline by geography")

    geo_counts = (
        filtered[filtered["Geography"] != ""]
        .groupby("Geography")
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
    if geo_counts.empty:
        st.info("No rows match the current filters.")
    else:
        fig = px.bar(
            geo_counts,
            x="Geography",
            y="Count",
            color_discrete_sequence=[SEQUENTIAL_BLUE],
        )
        fig.update_layout(xaxis_title=None, yaxis_title="Firms", showlegend=False)
        st.plotly_chart(fig, width='stretch')

    st.subheader("Firms sorted by geography")
    st.dataframe(
        filtered.sort_values(by=["Geography", "Firm"]).reset_index(drop=True),
        width='stretch',
        height=450,
    )

# ---------------------------------------------------------------------------
# By Asset Class
# ---------------------------------------------------------------------------
with tab_asset:
    st.subheader("Pipeline by asset class")

    ac_counts = (
        filtered[filtered["Asset Class"] != ""]
        .groupby("Asset Class")
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
    if ac_counts.empty:
        st.info("No rows match the current filters.")
    else:
        fig = px.bar(
            ac_counts,
            x="Asset Class",
            y="Count",
            color_discrete_sequence=[SEQUENTIAL_BLUE],
        )
        fig.update_layout(xaxis_title=None, yaxis_title="Firms", showlegend=False)
        st.plotly_chart(fig, width='stretch')

    st.subheader("Firms sorted by asset class")
    st.dataframe(
        filtered.sort_values(by=["Asset Class", "Sub Asset Class", "Firm"]).reset_index(drop=True),
        width='stretch',
        height=450,
    )

# ---------------------------------------------------------------------------
# Fundraising Timeline
# ---------------------------------------------------------------------------
with tab_fundraising:
    st.subheader("Fundraising timeline")
    st.caption(
        "The source pipeline didn't track fundraising timelines. Use the Data Entry "
        "tab to set **Fundraising Status** and **Target Close Date** per firm; this "
        "view populates as that data comes in."
    )

    has_dates = filtered["Target Close Date"].notna()
    with_dates = filtered[has_dates].sort_values("Target Close Date")

    status_counts = (
        filtered[filtered["Fundraising Status"] != ""]
        .groupby("Fundraising Status")
        .size()
        .reset_index(name="Count")
    )
    if not status_counts.empty:
        fig = px.bar(
            status_counts,
            x="Fundraising Status",
            y="Count",
            category_orders={"Fundraising Status": FUNDRAISING_STATUS_OPTIONS},
            color_discrete_sequence=[SEQUENTIAL_BLUE],
        )
        fig.update_layout(xaxis_title=None, yaxis_title="Firms", showlegend=False)
        st.plotly_chart(fig, width='stretch')

    if with_dates.empty:
        st.info("No target close dates entered yet.")
    else:
        fig2 = px.timeline(
            with_dates.assign(
                _end=with_dates["Target Close Date"] + pd.Timedelta(days=1)
            ),
            x_start="Target Close Date",
            x_end="_end",
            y="Firm",
            color="Stage",
            category_orders={"Stage": STAGE_OPTIONS},
            color_discrete_map=STAGE_COLOR_MAP,
        )
        fig2.update_yaxes(autorange="reversed", title=None)
        st.plotly_chart(fig2, width='stretch')

    st.subheader("Firms sorted by target close date")
    st.dataframe(
        filtered.sort_values(by=["Target Close Date", "Firm"], na_position="last").reset_index(
            drop=True
        ),
        width='stretch',
        height=450,
    )
