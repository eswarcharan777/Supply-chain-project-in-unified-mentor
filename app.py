"""Streamlit dashboard for APL Logistics delivery-performance analysis."""

from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from src.auth import current_role, has_role, logout, require_login
from src.database import database_status, initialize_database
from src.metrics import calculate_kpis, performance_by
from src.prediction import CATEGORICAL_COLUMNS, NUMERIC_COLUMNS, prediction_input_defaults, predict_delay_probability, train_delay_model
from src.routing import simulated_route_plan


st.set_page_config(
    page_title="APL Logistics | Delivery Performance",
    page_icon="🚚",
    layout="wide",
)

DATA_PATH = Path("data/processed/cleaned_logistics.csv")
DATABASE_PATH = Path("data/live/apl_logistics.db")
CATEGORY_COLORS = {"Early": "#10B981", "On Time": "#2563EB", "Delayed": "#DC2626"}
FILTER_KEYS = ["shipping_mode_filter", "market_filter", "region_filter", "country_filter", "segment_filter"]


@st.cache_data(show_spinner="Loading prepared logistics data...")
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    data["is_delayed"] = data["is_delayed"].astype(bool)
    data["is_on_time_or_early"] = data["is_on_time_or_early"].astype(bool)
    return data


@st.cache_resource(show_spinner="Training historical delay-risk model...")
def load_delay_model(data_path: str):
    return train_delay_model(load_data(data_path))


def option_values(data: pd.DataFrame, column: str) -> list[str]:
    return sorted(data[column].dropna().astype(str).unique().tolist())


def clear_filters() -> None:
    """Clear every dashboard filter in one action."""
    for key in FILTER_KEYS:
        st.session_state[key] = []


def apply_filters(data: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Dashboard filters")
    st.sidebar.caption("All charts and KPIs update from these selections.")
    st.sidebar.button("Clear all filters", on_click=clear_filters, use_container_width=True)

    selected_modes = st.sidebar.multiselect("Shipping mode", option_values(data, "Shipping Mode"), key="shipping_mode_filter")
    selected_markets = st.sidebar.multiselect("Market", option_values(data, "Market"), key="market_filter")
    selected_regions = st.sidebar.multiselect("Order region", option_values(data, "Order Region"), key="region_filter")
    selected_countries = st.sidebar.multiselect("Order country", option_values(data, "Order Country"), key="country_filter")
    selected_segments = st.sidebar.multiselect("Customer segment", option_values(data, "Customer Segment"), key="segment_filter")

    filtered = data.copy()
    selections = {
        "Shipping Mode": selected_modes,
        "Market": selected_markets,
        "Order Region": selected_regions,
        "Order Country": selected_countries,
        "Customer Segment": selected_segments,
    }
    for column, selected in selections.items():
        if selected:
            filtered = filtered[filtered[column].isin(selected)]
    st.sidebar.caption(f"Showing {len(filtered):,} of {len(data):,} shipments")
    if has_role("Analyst", "Admin"):
        st.sidebar.download_button(
            "Download filtered data (CSV)",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="apl_logistics_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.sidebar.caption("Filtered-data export requires an Analyst or Admin role.")
    return filtered


def percent_format(value: float) -> str:
    return f"{value:.2f}%"


def render_overview(data: pd.DataFrame) -> None:
    st.subheader("Delivery performance overview")
    kpis = calculate_kpis(data)
    metric_columns = st.columns(5)
    metric_columns[0].metric("Shipments", f"{kpis['total_shipments']:,}")
    metric_columns[1].metric("On-time or early", percent_format(kpis["on_time_delivery_rate"]))
    metric_columns[2].metric("Calculated delayed rate", percent_format(kpis["late_delivery_rate"]))
    metric_columns[3].metric("Average delay gap", f"{kpis['average_delivery_delay_days']:.2f} days")
    metric_columns[4].metric("Source late-risk ratio", percent_format(kpis["late_delivery_risk_ratio"]))

    st.caption(
        "Calculated delay uses actual minus scheduled shipping days. The source late-risk flag is shown separately because it uses a different definition."
    )

    left, right = st.columns(2)
    with left:
        category_counts = (
            data["delivery_category"].value_counts().rename_axis("delivery_category").reset_index(name="shipments")
        )
        category_chart = (
            alt.Chart(category_counts)
            .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
            .encode(
                y=alt.Y("delivery_category:N", sort=["Delayed", "On Time", "Early"], title=None),
                x=alt.X("shipments:Q", title="Shipments"),
                color=alt.Color("delivery_category:N", scale=alt.Scale(domain=list(CATEGORY_COLORS), range=list(CATEGORY_COLORS.values())), legend=None),
                tooltip=["delivery_category:N", alt.Tooltip("shipments:Q", format=",")],
            )
            .properties(title="Delivery classification")
        )
        st.altair_chart(category_chart, width="stretch")
    with right:
        status_counts = data["Delivery Status"].value_counts().rename_axis("Delivery Status").reset_index(name="shipments")
        status_chart = (
            alt.Chart(status_counts)
            .mark_arc(innerRadius=55)
            .encode(
                theta=alt.Theta("shipments:Q"),
                color=alt.Color("Delivery Status:N", legend=alt.Legend(title="Delivery status")),
                tooltip=["Delivery Status:N", alt.Tooltip("shipments:Q", format=",")],
            )
            .properties(title="Source delivery status")
        )
        st.altair_chart(status_chart, width="stretch")


def render_delay_risk(data: pd.DataFrame) -> None:
    st.subheader("Delay risk analysis")
    left, right = st.columns(2)
    with left:
        delay_histogram = (
            alt.Chart(data)
            .mark_bar(color="#2563EB")
            .encode(
                x=alt.X("delivery_delay_gap:Q", bin=alt.Bin(maxbins=14), title="Actual minus scheduled shipping days"),
                y=alt.Y("count():Q", title="Shipments"),
                tooltip=[alt.Tooltip("count():Q", title="Shipments", format=",")],
            )
            .properties(title="Distribution of delivery delay gaps")
        )
        st.altair_chart(delay_histogram, width="stretch")
    with right:
        risk_counts = data["Late_delivery_risk"].map({0: "No source risk", 1: "Source risk"}).value_counts().rename_axis("risk_status").reset_index(name="shipments")
        risk_chart = (
            alt.Chart(risk_counts)
            .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
            .encode(
                y=alt.Y("risk_status:N", title=None),
                x=alt.X("shipments:Q", title="Shipments"),
                color=alt.Color("risk_status:N", scale=alt.Scale(range=["#16A34A", "#F59E0B"]), legend=None),
                tooltip=["risk_status:N", alt.Tooltip("shipments:Q", format=",")],
            )
            .properties(title="Source late-delivery-risk flag")
        )
        st.altair_chart(risk_chart, width="stretch")


def render_shipping_mode(data: pd.DataFrame) -> None:
    st.subheader("Shipping mode comparison")
    summary = performance_by(data, "Shipping Mode")
    chart = (
        alt.Chart(summary)
        .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
        .encode(
            x=alt.X("Shipping Mode:N", sort="-y", title=None),
            y=alt.Y("delayed_delivery_rate:Q", title="Calculated delayed-delivery rate (%)"),
            color=alt.Color("average_delay_days:Q", scale=alt.Scale(scheme="orangered"), title="Avg. delay days"),
            tooltip=[
                "Shipping Mode:N",
                alt.Tooltip("shipments:Q", format=","),
                alt.Tooltip("delayed_delivery_rate:Q", format=".2f"),
                alt.Tooltip("on_time_delivery_rate:Q", format=".2f"),
                alt.Tooltip("average_delay_days:Q", format=".2f"),
            ],
        )
        .properties(title="Delay rate by shipping mode")
    )
    st.altair_chart(chart, width="stretch")
    st.dataframe(summary, width="stretch", hide_index=True)


def render_regional_analysis(data: pd.DataFrame) -> None:
    st.subheader("Regional and market diagnostics")
    grouping = st.radio("Analyze by", ["Order Region", "Market", "Order Country"], horizontal=True)
    summary = performance_by(data, grouping).sort_values("delayed_delivery_rate", ascending=False)
    display_summary = summary.head(20)
    chart = (
        alt.Chart(display_summary)
        .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
        .encode(
            y=alt.Y(f"{grouping}:N", sort="-x", title=None),
            x=alt.X("delayed_delivery_rate:Q", title="Calculated delayed-delivery rate (%)"),
            color=alt.Color("shipments:Q", scale=alt.Scale(scheme="blues"), title="Shipments"),
            tooltip=[
                f"{grouping}:N",
                alt.Tooltip("shipments:Q", format=","),
                alt.Tooltip("delayed_delivery_rate:Q", format=".2f"),
                alt.Tooltip("average_delay_days:Q", format=".2f"),
            ],
        )
        .properties(title=f"Top 20 delay-risk locations: {grouping}")
    )
    st.altair_chart(chart, width="stretch")
    st.dataframe(display_summary, width="stretch", hide_index=True)


def render_priority_matrix(data: pd.DataFrame) -> None:
    st.subheader("Regional priority matrix")
    st.caption("Prioritize regions that combine high shipment volume with a high calculated delayed-delivery rate.")
    summary = performance_by(data, "Order Region")
    chart = (
        alt.Chart(summary)
        .mark_circle(opacity=0.78)
        .encode(
            x=alt.X("shipments:Q", title="Shipment volume"),
            y=alt.Y("delayed_delivery_rate:Q", title="Calculated delayed-delivery rate (%)"),
            size=alt.Size("average_delay_days:Q", title="Average delay days", scale=alt.Scale(range=[80, 1500])),
            color=alt.Color("average_delay_days:Q", title="Average delay days", scale=alt.Scale(scheme="redyellowgreen", reverse=True)),
            tooltip=[
                "Order Region:N",
                alt.Tooltip("shipments:Q", format=","),
                alt.Tooltip("delayed_delivery_rate:Q", format=".2f"),
                alt.Tooltip("average_delay_days:Q", format=".2f"),
            ],
        )
        .properties(title="Volume versus delay-risk prioritization")
    )
    st.altair_chart(chart, width="stretch")


def render_geographic_risk_map(data: pd.DataFrame) -> None:
    st.subheader("Geographic delay-risk map")
    st.caption("Each circle represents a customer-location cluster. Larger and redder circles indicate more shipments and a higher calculated delayed-delivery rate.")
    map_data = data.copy()
    map_data["Latitude"] = pd.to_numeric(map_data["Latitude"], errors="coerce")
    map_data["Longitude"] = pd.to_numeric(map_data["Longitude"], errors="coerce")
    map_data = map_data.dropna(subset=["Latitude", "Longitude"])
    map_summary = (
        map_data.groupby(["Order Country", "Latitude", "Longitude"], as_index=False)
        .agg(
            shipments=("delivery_delay_gap", "size"),
            delayed_rate=("is_delayed", "mean"),
            average_delay_days=("delivery_delay_gap", "mean"),
        )
    )
    # Large raw datasets can contain thousands of coordinate clusters. Display the
    # highest-volume 750 locations to keep the map readable and responsive.
    map_summary = map_summary.sort_values("shipments", ascending=False).head(750).copy()
    map_summary["delayed_rate_pct"] = (map_summary["delayed_rate"] * 100).round(2)
    map_summary["average_delay_days"] = map_summary["average_delay_days"].round(2)
    map_summary["radius"] = map_summary["shipments"].clip(lower=1).pow(0.5) * 17000
    map_summary["color"] = map_summary["delayed_rate"].apply(
        lambda rate: [int(70 + 180 * rate), int(180 - 110 * rate), 90, 185]
    )

    if map_summary.empty:
        st.info("No valid coordinates are available for the selected filters.")
        return

    view_state = pdk.ViewState(
        latitude=float(map_summary["Latitude"].mean()),
        longitude=float(map_summary["Longitude"].mean()),
        zoom=1,
        pitch=0,
    )
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_summary,
        get_position="[Longitude, Latitude]",
        get_radius="radius",
        get_fill_color="color",
        pickable=True,
        opacity=0.75,
    )
    tooltip = {
        "html": "<b>{Order Country}</b><br/>Shipments: {shipments}<br/>Delayed rate: {delayed_rate_pct}%<br/>Average delay: {average_delay_days} days",
        "style": {"backgroundColor": "#111827", "color": "white"},
    }
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip), width="stretch")


def render_key_insights(data: pd.DataFrame) -> None:
    st.subheader("Decision-ready insights")
    mode_summary = performance_by(data, "Shipping Mode")
    region_summary = performance_by(data, "Order Region")
    highest_risk_mode = mode_summary.sort_values(["delayed_delivery_rate", "shipments"], ascending=[False, False]).iloc[0]
    material_regions = region_summary[region_summary["shipments"] >= 1000]
    if material_regions.empty:
        material_regions = region_summary
    highest_risk_region = material_regions.sort_values(["delayed_delivery_rate", "shipments"], ascending=[False, False]).iloc[0]

    first, second = st.columns(2)
    first.info(
        f"**Shipping-mode priority — {highest_risk_mode['Shipping Mode']}**  \n"
        f"{highest_risk_mode['delayed_delivery_rate']:.2f}% delayed across {int(highest_risk_mode['shipments']):,} shipments, "
        f"with an average delay gap of {highest_risk_mode['average_delay_days']:.2f} days."
    )
    second.warning(
        f"**Regional priority — {highest_risk_region['Order Region']}**  \n"
        f"{highest_risk_region['delayed_delivery_rate']:.2f}% delayed across {int(highest_risk_region['shipments']):,} shipments."
    )
    st.caption("Insights recalculate after filters are applied. They describe association in this historical dataset; they do not prove a single root cause.")


def render_recommendations(data: pd.DataFrame) -> None:
    st.subheader("Recommended operational actions")
    mode_summary = performance_by(data, "Shipping Mode")
    region_summary = performance_by(data, "Order Region")
    weakest_mode = mode_summary.sort_values(["delayed_delivery_rate", "shipments"], ascending=[False, False]).iloc[0]
    high_volume_region = region_summary.sort_values("shipments", ascending=False).iloc[0]

    st.markdown(
        f"1. **Review the {weakest_mode['Shipping Mode']} service promise.** It has a {weakest_mode['delayed_delivery_rate']:.2f}% calculated delayed-delivery rate across {int(weakest_mode['shipments']):,} shipments. Compare scheduled lead time with actual carrier performance before changing SLAs.\n"
        f"2. **Prioritize {high_volume_region['Order Region']} for operational monitoring.** It has the largest shipment volume in the current view ({int(high_volume_region['shipments']):,} shipments), so even modest delay reduction can affect many orders.\n"
        "3. **Use the regional priority matrix before allocating improvement effort.** High-volume, high-delay regions should be investigated before low-volume outliers.\n"
        "4. **Keep calculated delivery delay separate from the source risk flag.** The source field and actual-versus-scheduled calculation are not identical in this dataset."
    )
    with st.expander("Metric definitions and scope"):
        st.markdown(
            "- **Delivery delay gap:** actual shipping days minus scheduled shipping days.\n"
            "- **Delayed delivery:** a positive delivery delay gap.\n"
            "- **On-time or early:** a zero or negative delivery delay gap.\n"
            "- **Scope:** this dashboard diagnoses historical patterns; it does not predict future delays or prove root causes."
        )


def render_delay_prediction(data: pd.DataFrame) -> None:
    st.subheader("Machine-learning delay prediction")
    st.caption("Historical risk estimate using only fields available before delivery. It supports prioritization; it is not a guarantee of a future outcome.")
    model = load_delay_model(str(DATA_PATH))
    first, second, third = st.columns(3)
    first.metric("Validation accuracy", f"{model.accuracy * 100:.1f}%")
    second.metric("Validation ROC-AUC", f"{model.roc_auc:.3f}")
    third.metric("Model target", "Delayed delivery")

    defaults = prediction_input_defaults(data)
    with st.form("delay_prediction_form"):
        input_values: dict[str, object] = {}
        for index, column in enumerate(CATEGORICAL_COLUMNS):
            choices = option_values(data, column)
            default_index = choices.index(str(defaults[column])) if str(defaults[column]) in choices else 0
            input_values[column] = st.selectbox(column, choices, index=default_index, key=f"prediction_{index}")
        numeric_columns = st.columns(3)
        for index, column in enumerate(NUMERIC_COLUMNS):
            with numeric_columns[index % 3]:
                input_values[column] = st.number_input(column, value=float(defaults[column]), key=f"prediction_number_{index}")
        submitted = st.form_submit_button("Estimate delay risk", use_container_width=True)
    if submitted:
        probability = predict_delay_probability(model, input_values)
        severity = "High" if probability >= 0.70 else "Moderate" if probability >= 0.45 else "Lower"
        st.info(f"**{severity} predicted delay risk: {probability * 100:.1f}%**. Use this result to prioritize review, not to make an automated customer-impacting decision.")


def render_route_simulator(data: pd.DataFrame) -> None:
    st.subheader("Route optimization planning simulator")
    st.warning("Simulation only: the supplied dataset has customer coordinates, but no warehouse origin, road network, traffic, carrier cost, or service-time data. This creates a nearest-neighbour visit sequence, not a real navigation route.")
    first, second, third = st.columns(3)
    with first:
        origin_lat = st.number_input("Planning origin latitude", value=0.0, min_value=-90.0, max_value=90.0)
    with second:
        origin_lon = st.number_input("Planning origin longitude", value=0.0, min_value=-180.0, max_value=180.0)
    with third:
        stop_count = st.slider("High-volume stops", min_value=3, max_value=15, value=8)
    if st.button("Generate simulated visit plan", use_container_width=True):
        plan = simulated_route_plan(data, origin_lat, origin_lon, stop_count)
        st.metric("Simulated route distance", f"{plan['cumulative_distance_km'].iloc[-1]:,.1f} km")
        st.dataframe(plan, width="stretch", hide_index=True)


def render_live_data_api() -> None:
    st.subheader("Live database and API")
    status = database_status(DATABASE_PATH)
    left, right = st.columns(2)
    with left:
        st.metric("SQLite live-data rows", f"{int(status['rows']):,}" if status["ready"] else "Not initialized")
    with right:
        st.metric("API status", "Ready when uvicorn is running")
    st.code("python -m uvicorn api:app --reload", language="powershell")
    st.caption("Available endpoints: GET /health, GET /summary, and GET /shipments?limit=100. The local SQLite database is refreshed from the prepared CSV by an Admin.")
    if st.button("Refresh local database from prepared CSV", use_container_width=True):
        rows = initialize_database(DATABASE_PATH, DATA_PATH)
        st.success(f"Local SQLite database refreshed with {rows:,} shipments.")


def render_user_access() -> None:
    role = current_role()
    st.sidebar.divider()
    st.sidebar.caption(f"Signed in as **{role}**")
    st.sidebar.caption("Viewer: overview. Analyst: prediction and simulator. Admin: database refresh.")
    st.sidebar.button("Sign out", on_click=logout, use_container_width=True)


def main() -> None:
    role = require_login()
    render_user_access()
    st.title("APL Logistics: Delivery Performance Dashboard")
    st.write("Operational analytics for delivery performance, delay risk, shipping modes, and regional bottlenecks.")

    if not DATA_PATH.exists():
        st.error("Prepared data is missing. Run the Day 1 pipeline before starting the dashboard.")
        st.code("python run_day1.py --source 'C:\\path\\to\\APL_Logistics.csv'")
        st.stop()

    raw_data = load_data(str(DATA_PATH))
    data = apply_filters(raw_data)
    if data.empty:
        st.warning("No shipments match the selected filters. Clear one or more filters and try again.")
        st.stop()

    render_overview(data)
    st.divider()
    render_delay_risk(data)
    st.divider()
    render_shipping_mode(data)
    st.divider()
    render_regional_analysis(data)
    st.divider()
    render_priority_matrix(data)
    st.divider()
    render_geographic_risk_map(data)
    st.divider()
    render_key_insights(data)
    st.divider()
    render_recommendations(data)
    if has_role("Analyst", "Admin"):
        st.divider()
        render_delay_prediction(data)
        st.divider()
        render_route_simulator(data)
    if has_role("Admin"):
        st.divider()
        render_live_data_api()


if __name__ == "__main__":
    main()
