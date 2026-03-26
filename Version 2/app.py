import math

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="v2: OpEx/CapEx + ROI Simulator", layout="wide")


def _clamp_float(x: float, lo: float, hi: float) -> float:
    if not math.isfinite(x):
        return lo
    return max(lo, min(hi, x))


def build_cost_plan(year1_opex: float, year1_capex: float, annual_change_pct: float, years: int = 5) -> pd.DataFrame:
    r = annual_change_pct / 100.0
    t = np.arange(years, dtype=float)  # 0..years-1
    factor = (1.0 + r) ** t

    opex = year1_opex * factor
    capex = year1_capex * factor
    total = opex + capex
    cumulative = np.cumsum(total)

    return pd.DataFrame(
        {
            "Year": np.arange(1, years + 1, dtype=int),
            "OpEx ($)": np.round(opex, 2),
            "CapEx ($)": np.round(capex, 2),
            "Total Cost ($)": np.round(total, 2),
            "Cumulative Cost ($)": np.round(cumulative, 2),
        }
    )


def fmt_money(x: float) -> str:
    try:
        return f"${x:,.0f}"
    except Exception:
        return "—"


def fmt_pct(x: float) -> str:
    try:
        return f"{x*100:,.1f}%"
    except Exception:
        return "—"


YEARS = 5
DEFAULT_TANGIBLE_GROWTH_PCT = 0.0
DEFAULT_INTANGIBLE_GROWTH_PCT = 2.0

st.title("5‑Year Financial Plan Simulator (v2)")
st.caption("Keeps the existing cost projection + $/year chart, and adds a tangible vs. intangible returns model + ROI%/year chart.")

with st.sidebar:
    st.subheader("Inputs (required)")
    year1_opex = st.number_input("1st year OpEx ($)", min_value=0.0, value=18_000.0, step=500.0)
    year1_capex = st.number_input("1st year CapEx ($)", min_value=0.0, value=5_000.0, step=500.0)
    annual_change_pct = st.number_input("Annual change (%)", value=5.0, step=0.5)

    st.divider()
    st.subheader("Tangible returns assumptions")
    tangible_mode = st.radio("Tangible benefit model", ["Annual benefit ($)", "Hours saved model"], index=0)

    tangible_realization_pct = st.number_input(
        "Tangible benefit realization (%)",
        min_value=0.0,
        max_value=100.0,
        value=80.0,
        step=5.0,
        help="Conservative haircut: not all time/process improvements turn into measurable dollars.",
    )
    tangible_realization = float(tangible_realization_pct) / 100.0

    if tangible_mode == "Annual benefit ($)":
        annual_tangible_benefit = st.number_input("Year 1 tangible benefit ($)", min_value=0.0, value=25_000.0, step=1_000.0)
        tangible_growth_pct = st.number_input(
            "Tangible benefit growth (%/yr)",
            value=DEFAULT_TANGIBLE_GROWTH_PCT,
            step=1.0,
        )
    else:
        team_size = st.number_input("Team size (people)", min_value=1, value=5, step=1)
        hours_saved_per_person_per_week = st.number_input("Hours saved / person / week", min_value=0.0, value=1.0, step=0.25)
        loaded_cost_per_hour = st.number_input("Loaded cost ($/hour)", min_value=0.0, value=60.0, step=5.0)
        working_weeks = st.number_input("Working weeks/year", min_value=1, max_value=52, value=48, step=1)

        # Keep behavior aligned with the original app (hours-saved produces a flat annual benefit).
        tangible_growth_pct = st.number_input(
            "Tangible growth (%/yr) (optional)",
            value=0.0,
            step=1.0,
            help="If you don’t want growth, leave at 0%.",
        )

    st.divider()
    st.subheader("Intangible returns assumptions")
    st.caption("Intangibles are not guaranteed cash flows. This model monetizes them using a conservative realization + growth.")
    intangible_realization_pct = st.number_input(
        "Intangible realization (%)",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=5.0,
        help="How much of intangible value you assume converts to measurable business outcomes.",
    )
    intangible_realization = float(intangible_realization_pct) / 100.0
    intangible_year1 = st.number_input("Year 1 intangible return ($)", min_value=0.0, value=10_000.0, step=500.0)
    intangible_growth_pct = st.number_input("Intangible growth (%/yr)", value=DEFAULT_INTANGIBLE_GROWTH_PCT, step=1.0)

    st.divider()
    st.subheader("Discount rate")
    discount_rate_pct = st.number_input("Discount rate for NPV (%, %/yr)", min_value=0.0, value=10.0, step=1.0)
    discount_rate = float(discount_rate_pct) / 100.0


cost_df = build_cost_plan(float(year1_opex), float(year1_capex), float(annual_change_pct), years=YEARS)

# ----------------------------
# Build tangible returns series
# ----------------------------
t_idx = np.arange(YEARS, dtype=float)  # 0..4

if tangible_mode == "Annual benefit ($)":
    tangible_benefits_year1 = float(annual_tangible_benefit)
    tangible_growth = float(tangible_growth_pct) / 100.0
    tangible_raw = tangible_benefits_year1 * (1.0 + tangible_growth) ** t_idx
else:
    annual_hours_value = float(team_size) * float(hours_saved_per_person_per_week) * float(working_weeks) * float(loaded_cost_per_hour)
    tangible_growth = float(tangible_growth_pct) / 100.0
    tangible_raw = annual_hours_value * (1.0 + tangible_growth) ** t_idx

tangible_returns = tangible_raw * tangible_realization

# ----------------------------
# Build intangible returns series
# ----------------------------
intangible_growth = float(intangible_growth_pct) / 100.0
intangible_returns = float(intangible_year1) * (1.0 + intangible_growth) ** t_idx * intangible_realization

# ----------------------------
# Combine and compute ROI
# ----------------------------
returns_df = pd.DataFrame(
    {
        "Year": cost_df["Year"],
        "Tangible Return ($)": np.round(tangible_returns, 2),
        "Intangible Return ($)": np.round(intangible_returns, 2),
    }
)
returns_df["Total Return ($)"] = np.round(returns_df["Tangible Return ($)"] + returns_df["Intangible Return ($)"], 2)

costs = cost_df["Total Cost ($)"].to_numpy(dtype=float)
total_returns = returns_df["Total Return ($)"].to_numpy(dtype=float)

net = total_returns - costs
roi_undiscounted = (total_returns.sum() - costs.sum()) / costs.sum() if costs.sum() > 0 else float("nan")

disc = (1.0 + discount_rate) ** np.arange(1, YEARS + 1, dtype=float)
npv = float((net / disc).sum())

# ROI% per year for the ROI chart
roi_pct_per_year = np.full(YEARS, np.nan, dtype=float)
mask_cost = costs > 0
roi_pct_per_year[mask_cost] = (net[mask_cost] / costs[mask_cost]) * 100.0
returns_df["ROI % (undiscounted)"] = np.round(roi_pct_per_year, 2)

output_df = cost_df.merge(returns_df, on="Year", how="left")

# ----------------------------
# UI: cost table + chart (existing items)
# ----------------------------
left, right = st.columns([1.15, 1])
with left:
    st.subheader("Cash flow table (Costs) — Years 1–5")
    st.dataframe(
        cost_df.rename(columns={"Total Cost ($)": "Total ($)", "Cumulative Cost ($)": "Cumulative ($)"}),
        width="stretch",
        hide_index=True,
    )

with right:
    st.subheader("5‑year totals (Costs)")
    total_opex = float(cost_df["OpEx ($)"].sum())
    total_capex = float(cost_df["CapEx ($)"].sum())
    total_cost = float(cost_df["Total Cost ($)"].sum())
    st.metric("OpEx (5‑yr)", fmt_money(total_opex))
    st.metric("CapEx (5‑yr)", fmt_money(total_capex))
    st.metric("Total cost / TCO (5‑yr)", fmt_money(total_cost))

st.subheader("Chart (existing) — x = $, y = year")
chart_df = cost_df.melt(
    id_vars=["Year"],
    value_vars=["OpEx ($)", "CapEx ($)", "Total Cost ($)"],
    var_name="Type",
    value_name="Dollars",
)
chart_df["Type"] = chart_df["Type"].replace({"Total Cost ($)": "Total ($)"})
chart_df["Year"] = chart_df["Year"].apply(lambda y: f"Year {int(y)}")

cost_fig = px.bar(
    chart_df,
    x="Dollars",
    y="Year",
    color="Type",
    orientation="h",
    barmode="group",
    height=420,
)
cost_fig.update_layout(xaxis_title="Dollars ($)", yaxis_title="Year", legend_title_text="")
st.plotly_chart(cost_fig, width="stretch")

# ----------------------------
# New: Tangible vs Intangible returns table
# ----------------------------
st.subheader("Table of tangible vs intangible returns (Years 1–5)")
st.dataframe(
    returns_df.drop(columns=["ROI % (undiscounted)"]),
    width="stretch",
    hide_index=True,
)

left2, right2 = st.columns([1.1, 1])
with left2:
    st.subheader("5‑year totals (Returns)")
    total_tangible = float(returns_df["Tangible Return ($)"].sum())
    total_intangible = float(returns_df["Intangible Return ($)"].sum())
    total_total_return = float(returns_df["Total Return ($)"].sum())
    st.metric("Tangible returns (5‑yr)", fmt_money(total_tangible))
    st.metric("Intangible returns (5‑yr)", fmt_money(total_intangible))
    st.metric("Total returns (5‑yr)", fmt_money(total_total_return))

with right2:
    st.subheader("5‑year ROI (summary)")
    total_net = float(net.sum())
    roi_text = "—" if not math.isfinite(roi_undiscounted) else f"{roi_undiscounted*100:,.1f}%"
    st.metric("5‑yr net (returns − costs)", fmt_money(total_net))
    st.metric("ROI (undiscounted, overall)", roi_text)
    st.caption(f"NPV (discount {discount_rate_pct:.0f}%): {fmt_money(npv)}")

# ----------------------------
# New: ROI chart (x = ROI %, y = year)
# ----------------------------
st.subheader("Chart (new) — x = ROI %, y = year")
roi_chart_df = returns_df[["Year", "ROI % (undiscounted)"]].copy()
roi_chart_df["Year"] = roi_chart_df["Year"].apply(lambda y: f"Year {int(y)}")

roi_fig = px.bar(
    roi_chart_df,
    x="ROI % (undiscounted)",
    y="Year",
    orientation="h",
    color="ROI % (undiscounted)",
    color_continuous_scale="RdYlGn",
    height=420,
)
roi_fig.update_layout(xaxis_title="ROI % (returns − costs) / costs", yaxis_title="Year", showlegend=False)
st.plotly_chart(roi_fig, width="stretch")


with st.expander("Justified assumptions (paste into report)", expanded=True):
    st.markdown(
        """
**Cost assumptions (OpEx/CapEx)**  
- **OpEx**: recurring costs such as subscriptions, support, and periodic training. These are typically predictable and scale gradually with usage.  
- **CapEx**: one-time enablement/setup costs (initial implementation effort, initial purchases).  
- **Annual change (%)**: represents price drift and scaling. When exact vendor contracts aren’t known, a modest rate (e.g., 3–8%) is defensible.  

**Tangible returns assumptions**  
- **Quantified as** either (a) an **annual benefit $** or (b) an **hours-saved** model using a loaded labor rate.  
- **Tangible realization (%)** applies a conservative haircut because not all saved time becomes measurable cash value.  
- **Tangible growth (%/yr)** models how benefits scale as usage grows (set to 0% if you want a flat assumption).  

**Intangible returns assumptions**  
- Intangibles (brand trust, improved satisfaction, reduced risk) are harder to convert directly into cash flows.  
- This model monetizes intangibles using **Intangible realization (%)** and **Intangible growth (%/yr)** so your ROI remains grounded and defensible.  

**ROI definitions**  
- Per-year ROI % (shown on the ROI chart):  
  \n`ROI%_t = (Return_t − Cost_t) / Cost_t * 100`  
- Overall ROI and NPV use the sum of yearly net cash flows, with NPV discounting by the selected discount rate.
        """.strip()
    )


download_df = output_df.rename(
    columns={
        "Total Cost ($)": "Total Cost ($)",
        "Tangible Return ($)": "Tangible Return ($)",
        "Intangible Return ($)": "Intangible Return ($)",
        "Total Return ($)": "Total Return ($)",
        "ROI % (undiscounted)": "ROI % (undiscounted)",
    }
)

st.download_button(
    "Download results as CSV",
    data=download_df.to_csv(index=False),
    file_name="five_year_plan_v2.csv",
    mime="text/csv",
    key="download_results_v2",
)

