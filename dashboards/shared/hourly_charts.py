"""
Harris Farm Hub — Shared Hourly Trading Pattern Charts
Reusable component: day-of-week revenue, hourly revenue, and trading heatmap.
Used by all transaction dashboards (Store Ops, Product Intel, Revenue Bridge, Buying Hub).
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# Canonical day ordering (Mon-Sun) — used to force Plotly x-axis order.
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]


def render_hourly_analysis(query_fn, store_id, start, end,
                           key_prefix="hourly", hierarchy=None,
                           time_filters=None):
    """Render hourly trading pattern charts.

    Args:
        query_fn: callable that runs named queries — signature: query_fn(name, **kwargs).
        store_id: store ID string (e.g., "28").
        start: start date string (YYYY-MM-DD).
        end: end date string (YYYY-MM-DD).
        key_prefix: unique prefix for widget keys (prevents collisions).
        hierarchy: dict from render_hierarchy_filter() with dept_code,
                   major_code, minor_code, hfm_item_code, product_number,
                   day_type keys (all optional).
        time_filters: dict from render_time_filter() with day_of_week_names,
                      hour_start, hour_end, season_names, quarter_nos,
                      month_nos keys (all optional).
    """
    # Build base kwargs for all hourly queries
    base_kwargs = {"store_id": store_id, "start": start, "end": end}
    if hierarchy:
        for key in ["dept_code", "major_code", "minor_code",
                     "hfm_item_code", "product_number", "day_type"]:
            if hierarchy.get(key):
                base_kwargs[key] = hierarchy[key]
    if time_filters:
        for key in ["day_of_week_names", "hour_start", "hour_end",
                     "season_names", "quarter_nos", "month_nos"]:
            if time_filters.get(key) is not None:
                base_kwargs[key] = time_filters[key]

    col_dow, col_hour = st.columns(2)

    with col_dow:
        st.markdown("**Revenue by Day of Week**")
        try:
            dow_data = query_fn("fiscal_day_of_week", **base_kwargs)
            if dow_data:
                df_dow = pd.DataFrame(dow_data)
                df_dow["day_type"] = df_dow["businessday"].apply(
                    lambda x: "Business Day" if x == "Y" else "Weekend")

                # Force Mon-Sun ordering via Categorical dtype
                df_dow["dayofweekname"] = pd.Categorical(
                    df_dow["dayofweekname"], categories=DAY_ORDER, ordered=True)
                df_dow = df_dow.sort_values("dayofweekname")

                fig_dow = px.bar(
                    df_dow, x="dayofweekname", y="revenue",
                    color="day_type",
                    category_orders={"dayofweekname": DAY_ORDER},
                    color_discrete_map={
                        "Business Day": "#0d9488",
                        "Weekend": "#7c3aed",
                    },
                    labels={
                        "dayofweekname": "Day",
                        "revenue": "Revenue ($)",
                        "day_type": "",
                    },
                )
                fig_dow.update_layout(
                    height=350, legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig_dow,
                                key=f"{key_prefix}_dow_chart")

                # Data coverage indicator
                day_names = set(df_dow["dayofweekname"].tolist())
                has_sat = "Saturday" in day_names
                has_sun = "Sunday" in day_names
                n_days = len(day_names)
                if n_days < 7:
                    missing = [d for d in DAY_ORDER if d not in day_names]
                    st.caption(f"Data covers {n_days}/7 days. "
                               f"Missing: {', '.join(missing)}")
                if has_sat and has_sun:
                    sat_rev = df_dow.loc[
                        df_dow["dayofweekname"] == "Saturday", "revenue"
                    ].sum()
                    sun_rev = df_dow.loc[
                        df_dow["dayofweekname"] == "Sunday", "revenue"
                    ].sum()
                    st.caption(f"Weekend included: Sat ${sat_rev:,.0f} | "
                               f"Sun ${sun_rev:,.0f}")
            else:
                st.info("No day-of-week data.")
        except Exception as e:
            st.error(f"Day-of-week query failed: {e}")

    with col_hour:
        st.markdown("**Revenue by Hour — Business Day vs Weekend**")
        try:
            hour_data = query_fn("fiscal_hourly_by_day_type",
                                 **base_kwargs)
            if hour_data:
                df_hour = pd.DataFrame(hour_data)
                df_hour["day_type"] = df_hour["day_type"].apply(
                    lambda x: "Business Day" if x == "Y" else "Weekend")
                fig_hour = px.bar(
                    df_hour, x="hour_of_day", y="revenue",
                    color="day_type", barmode="group",
                    category_orders={"day_type": ["Business Day", "Weekend"]},
                    color_discrete_map={
                        "Business Day": "#0d9488",
                        "Weekend": "#7c3aed",
                    },
                    labels={
                        "hour_of_day": "Hour",
                        "revenue": "Revenue ($)",
                        "day_type": "",
                    },
                )
                fig_hour.update_layout(
                    height=350, legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig_hour,
                                key=f"{key_prefix}_hour_chart")

                # Confirm both day types present
                types_present = set(df_hour["day_type"].unique())
                if "Weekend" not in types_present:
                    st.warning("Weekend data missing from hourly view.")
            else:
                st.info("No hourly data.")
        except Exception as e:
            st.error(f"Hourly query failed: {e}")

    # Hourly heatmap (Day x Hour)
    st.markdown("**Trading Heatmap — Day of Week x Hour of Day**")
    try:
        heatmap_data = query_fn("fiscal_hourly_heatmap",
                                **base_kwargs)
        if heatmap_data:
            df_hm = pd.DataFrame(heatmap_data)
            pivot = df_hm.pivot_table(
                index="dayofweekname", columns="hour_of_day",
                values="revenue", aggfunc="sum", fill_value=0,
            )
            # Order days Mon-Sun
            pivot = pivot.reindex([d for d in DAY_ORDER if d in pivot.index])

            fig_hm = px.imshow(
                pivot,
                labels={"x": "Hour", "y": "Day", "color": "Revenue ($)"},
                color_continuous_scale="Teal",
                aspect="auto",
            )
            fig_hm.update_layout(height=300)
            st.plotly_chart(fig_hm,
                            key=f"{key_prefix}_heatmap_chart")

            # Show heatmap coverage
            hm_days = set(pivot.index.tolist())
            if len(hm_days) < 7:
                missing = [d for d in DAY_ORDER if d not in hm_days]
                st.caption(f"Heatmap covers {len(hm_days)}/7 days. "
                           f"Missing: {', '.join(missing)}")
        else:
            st.info("No heatmap data.")
    except Exception as e:
        st.error(f"Heatmap query failed: {e}")

    # Diagnostic data expander
    with st.expander("View raw trading pattern data"):
        try:
            raw = query_fn("fiscal_day_of_week", **base_kwargs)
            if raw:
                df_raw = pd.DataFrame(raw)
                st.markdown(f"**Query returned {len(df_raw)} day(s)** "
                            f"for store {store_id}, {start} to {end}")
                st.dataframe(
                    df_raw[["dayofweekno", "dayofweekname", "businessday",
                            "weekend", "revenue", "transactions"]].style.format({
                        "revenue": "${:,.0f}",
                        "transactions": "{:,.0f}",
                    }),
                )
                day_names = set(df_raw["dayofweekname"])
                if "Saturday" in day_names and "Sunday" in day_names:
                    st.success("Weekend data confirmed: Saturday and Sunday included.")
                else:
                    missing = {"Saturday", "Sunday"} - day_names
                    st.error(f"Weekend data MISSING: {', '.join(missing)}")
            else:
                st.warning("No data returned from fiscal_day_of_week query.")
                st.code(f"Query params: {base_kwargs}")
        except Exception as e:
            st.error(f"Diagnostic query failed: {e}")
