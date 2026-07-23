"""PI Pipeline Dashboard.

Run with: streamlit run app.py
"""

import datetime as dt
import hashlib

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_sortables import sort_items

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
from data_utils import blank_template, load_data, parse_uploaded_csv, save_data, stage_sort_key
from pptx_export import build_bar_chart_pptx, build_filter_footnote

st.set_page_config(page_title="PI Pipeline Dashboard", layout="wide")

if "df" not in st.session_state:
    st.session_state.df = load_data()


def refresh():
    st.session_state.df = load_data()


def gantt_bars(df: pd.DataFrame) -> pd.DataFrame:
    """Bar span = Raise Start Date -> Target Close Date where both are set.

    Falls back to a one-day sliver at Target Close Date when there's no
    (valid) start date, so rows with partial data still show up.
    """
    out = df.copy()
    out["_start"] = out["Raise Start Date"].fillna(out["Target Close Date"])
    out["_end"] = out["Target Close Date"]
    no_real_span = out["_start"] >= out["_end"]
    out.loc[no_real_span, "_end"] = out.loc[no_real_span, "_start"] + pd.Timedelta(days=1)
    return out


st.title("PI Pipeline Dashboard")

(
    tab_entry,
    tab_overview,
    tab_conviction,
    tab_geo,
    tab_asset,
    tab_fundraising,
    tab_forward_cal,
) = st.tabs(
    [
        "📋 Data Entry",
        "📊 Overview",
        "🎯 By Conviction",
        "🌍 By Geography",
        "🏢 By Asset Class",
        "📅 Fundraising Timeline",
        "🗓️ Forward Calendar",
    ]
)

# ---------------------------------------------------------------------------
# Data Entry
# ---------------------------------------------------------------------------
with tab_entry:
    with st.expander("📥 Start from a blank template or bulk-upload a CSV"):
        st.download_button(
            "⬇️ Download blank template",
            data=blank_template().to_csv(index=False),
            file_name="pi_pipeline_template.csv",
            mime="text/csv",
        )

        uploaded = st.file_uploader(
            "Upload a filled-in CSV to skip manual entry",
            type=["csv"],
            key="csv_uploader",
        )
        if uploaded is not None:
            try:
                new_df, upload_warnings = parse_uploaded_csv(uploaded)
            except ValueError as e:
                st.error(str(e))
            else:
                for w in upload_warnings:
                    st.warning(w)
                st.write(f"Parsed **{len(new_df)}** rows from `{uploaded.name}`.")
                mode = st.radio(
                    "How should this be applied?",
                    ["Replace all existing data", "Append to existing data"],
                    horizontal=True,
                    key="csv_upload_mode",
                )
                if st.button("Apply upload", type="primary", key="apply_csv_upload"):
                    result = (
                        new_df
                        if mode == "Replace all existing data"
                        else pd.concat([st.session_state.df, new_df], ignore_index=True)
                    )
                    save_data(result)
                    st.session_state.df = load_data()
                    st.success(f"Pipeline now has {len(st.session_state.df)} firms.")
                    st.rerun()

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
            "Raise Start Date": st.column_config.DateColumn(),
            "Target Close Date": st.column_config.DateColumn(),
            "Next Follow Up Date": st.column_config.DateColumn(),
            "On Forward Calendar": st.column_config.CheckboxColumn(
                "On Forward Calendar?", help="Also settable by dragging in the Forward Calendar tab."
            ),
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

active_filters = {
    "Stage": f_stage,
    "Asset Class": f_asset,
    "Geography": f_geo,
    "Fundraising Status": f_fundraising,
    "Client Invested": None if f_invested == "All" else f_invested,
    "Search": f_search,
}

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
        st.plotly_chart(fig, width='stretch', key="chart_conviction")

        cats = [s for s in STAGE_OPTIONS if s in counts["Stage"].unique()]
        pivot = counts.pivot(index="Stage", columns="Asset Class", values="Count").reindex(cats).fillna(0)
        series = {ac: pivot[ac].astype(int).tolist() for ac in pivot.columns}
        st.download_button(
            "⬇️ Export exhibit to PPTX",
            data=build_bar_chart_pptx(
                "Pipeline by Conviction (Stage)",
                cats,
                series,
                build_filter_footnote(active_filters, len(filtered)),
                stacked=True,
            ),
            file_name="pipeline_by_conviction.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            key="pptx_conviction",
        )

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
        st.plotly_chart(fig, width='stretch', key="chart_geography")

        st.download_button(
            "⬇️ Export exhibit to PPTX",
            data=build_bar_chart_pptx(
                "Pipeline by Geography",
                geo_counts["Geography"].tolist(),
                {"Firms": geo_counts["Count"].astype(int).tolist()},
                build_filter_footnote(active_filters, len(filtered)),
            ),
            file_name="pipeline_by_geography.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            key="pptx_geo",
        )

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
        st.plotly_chart(fig, width='stretch', key="chart_asset_class")

        st.download_button(
            "⬇️ Export exhibit to PPTX",
            data=build_bar_chart_pptx(
                "Pipeline by Asset Class",
                ac_counts["Asset Class"].tolist(),
                {"Firms": ac_counts["Count"].astype(int).tolist()},
                build_filter_footnote(active_filters, len(filtered)),
            ),
            file_name="pipeline_by_asset_class.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            key="pptx_asset",
        )

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
        "tab to set **Fundraising Status**, **Raise Start Date**, and **Target Close "
        "Date** per firm; this view populates as that data comes in. Bars span the "
        "actual raise window (Raise Start Date to Target Close Date) where both are "
        "set."
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
        st.plotly_chart(fig, width='stretch', key="chart_fundraising_status")

        st.download_button(
            "⬇️ Export exhibit to PPTX",
            data=build_bar_chart_pptx(
                "Pipeline by Fundraising Status",
                status_counts["Fundraising Status"].tolist(),
                {"Firms": status_counts["Count"].astype(int).tolist()},
                build_filter_footnote(active_filters, len(filtered)),
            ),
            file_name="pipeline_by_fundraising_status.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            key="pptx_fundraising",
        )

    if with_dates.empty:
        st.info("No target close dates entered yet.")
    else:
        fig2 = px.timeline(
            gantt_bars(with_dates),
            x_start="_start",
            x_end="_end",
            y="Firm",
            color="Stage",
            category_orders={"Stage": STAGE_OPTIONS},
            color_discrete_map=STAGE_COLOR_MAP,
        )
        fig2.update_yaxes(autorange="reversed", title=None)
        st.plotly_chart(fig2, width='stretch', key="chart_fundraising_gantt")

    st.subheader("Firms sorted by target close date")
    st.dataframe(
        filtered.sort_values(by=["Target Close Date", "Firm"], na_position="last").reset_index(
            drop=True
        ),
        width='stretch',
        height=450,
    )

# ---------------------------------------------------------------------------
# Forward Calendar
# ---------------------------------------------------------------------------
with tab_forward_cal:
    st.subheader("Forward Calendar")
    st.caption(
        "Drag firms from **Filtered results** (driven by the sidebar filters) into "
        "**Forward Calendar** to build a curated set. Membership persists across "
        "filter changes - e.g. filter for one search, drag a few in, change the "
        "filter to a different search, drag more in. Drag an item back out to "
        "remove it."
    )

    all_firms_df = st.session_state.df
    calendar_items = sorted(all_firms_df.loc[all_firms_df["On Forward Calendar"], "Firm"].tolist())
    source_items = sorted(filtered.loc[~filtered["On Forward Calendar"], "Firm"].tolist())

    # Force a fresh mount whenever the true persisted state or the sidebar
    # filter changes, so the board always opens showing the current truth
    # rather than stale drag state from a previous mount.
    fingerprint = hashlib.md5(
        ("|".join(source_items) + "::" + "|".join(calendar_items)).encode()
    ).hexdigest()[:12]

    board = sort_items(
        [
            {"header": f"🔍 Filtered results ({len(source_items)})", "items": source_items},
            {"header": f"🗓️ Forward Calendar ({len(calendar_items)})", "items": calendar_items},
        ],
        multi_containers=True,
        key=f"forward_cal_board_{fingerprint}",
    )

    new_calendar_set = set(board[1]["items"])
    old_calendar_set = set(calendar_items)
    added = new_calendar_set - old_calendar_set
    removed = old_calendar_set - new_calendar_set

    if added or removed:
        updated = all_firms_df.copy()
        updated.loc[updated["Firm"].isin(added), "On Forward Calendar"] = True
        updated.loc[updated["Firm"].isin(removed), "On Forward Calendar"] = False
        save_data(updated)
        st.session_state.df = load_data()
        st.rerun()

    st.divider()

    cal_df = st.session_state.df[st.session_state.df["On Forward Calendar"]].copy()
    if cal_df.empty:
        st.info("Nothing on the Forward Calendar yet - drag firms in above.")
    else:
        if st.button("🗑️ Clear Forward Calendar"):
            cleared = st.session_state.df.copy()
            cleared["On Forward Calendar"] = False
            save_data(cleared)
            st.session_state.df = load_data()
            st.rerun()

        has_dates = cal_df["Target Close Date"].notna()
        with_dates = cal_df[has_dates].sort_values("Target Close Date")
        without_dates = cal_df[~has_dates].sort_values("Firm")

        if not with_dates.empty:
            fig = px.timeline(
                gantt_bars(with_dates),
                x_start="_start",
                x_end="_end",
                y="Firm",
                color="Stage",
                category_orders={"Stage": STAGE_OPTIONS},
                color_discrete_map=STAGE_COLOR_MAP,
            )
            fig.update_yaxes(autorange="reversed", title=None)
            st.plotly_chart(fig, width='stretch', key="chart_forward_calendar_gantt")

        display_cols = [
            "Firm",
            "Stage",
            "Asset Class",
            "Geography",
            "Fundraising Status",
            "Raise Start Date",
            "Target Close Date",
            "Commentary",
        ]

        st.subheader("By quarter")
        if with_dates.empty:
            st.caption("No Forward Calendar firms have a Target Close Date yet.")
        else:
            with_dates = with_dates.assign(
                _quarter=with_dates["Target Close Date"].dt.to_period("Q").astype(str)
            )
            for quarter in sorted(with_dates["_quarter"].unique()):
                grp = with_dates[with_dates["_quarter"] == quarter].sort_values("Target Close Date")
                st.markdown(f"**{quarter}** ({len(grp)})")
                st.dataframe(grp[display_cols].reset_index(drop=True), width='stretch')

        if not without_dates.empty:
            st.markdown(f"**Unscheduled** ({len(without_dates)})")
            st.caption("Set a Target Close Date in Data Entry to place these on the calendar.")
            st.dataframe(without_dates[display_cols].reset_index(drop=True), width='stretch')
