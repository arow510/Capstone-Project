import math

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="5-Year OpEx/CapEx + ROI Simulator", layout="wide")


def _clamp_float(x: float, lo: float, hi: float) -> float:
    if not math.isfinite(x):
        return lo
    return max(lo, min(hi, x))


def build_plan(year1_opex: float, year1_capex: float, annual_change_pct: float, years: int = 5) -> pd.DataFrame:
    r = annual_change_pct / 100.0
    t = np.arange(years, dtype=float)  # 0..years-1
    factor = (1.0 + r) ** t

    opex = year1_opex * factor
    capex = year1_capex * factor
    total = opex + capex
    cumulative = np.cumsum(total)

    df = pd.DataFrame(
        {
            "Year": np.arange(1, years + 1, dtype=int),
            "OpEx ($)": np.round(opex, 2),
            "CapEx ($)": np.round(capex, 2),
            "Total ($)": np.round(total, 2),
            "Cumulative ($)": np.round(cumulative, 2),
        }
    )
    return df


def fmt_money(x: float) -> str:
    try:
        return f"${x:,.0f}"
    except Exception:
        return "—"


st.title("5‑Year Financial Plan Simulator (OpEx / CapEx / ROI)")
st.caption("Enter Year‑1 costs and an annual change rate. The table + chart update instantly.")

with st.sidebar:
    st.subheader("Inputs (required)")
    year1_opex = st.number_input("1st year OpEx ($)", min_value=0.0, value=18_000.0, step=500.0)
    year1_capex = st.number_input("1st year CapEx ($)", min_value=0.0, value=5_000.0, step=500.0)
    annual_change_pct = st.number_input("Annual change (%)", value=5.0, step=0.5)
    annual_change_pct = _clamp_float(float(annual_change_pct), -100.0, 1000.0)

    st.divider()
    st.subheader("ROI assumptions (editable)")
    st.caption("Costs come from the plan. Benefits are your assumptions.")
    benefit_mode = st.radio("Benefit model", ["Annual benefit ($)", "Hours saved model"], index=0)

    if benefit_mode == "Annual benefit ($)":
        annual_benefit = st.number_input("Annual benefit ($)", min_value=0.0, value=25_000.0, step=1_000.0)
        benefit_growth_pct = st.number_input("Annual benefit change (%)", value=0.0, step=1.0)
        benefit_growth_pct = _clamp_float(float(benefit_growth_pct), -100.0, 1000.0)
        realization_pct = st.number_input("Benefit realization (%)", min_value=0.0, max_value=100.0, value=80.0, step=5.0)
        realization = float(realization_pct) / 100.0
    else:
        team_size = st.number_input("Team size (people)", min_value=1, value=5, step=1)
        hours_saved_per_person_per_week = st.number_input("Hours saved / person / week", min_value=0.0, value=1.0, step=0.25)
        loaded_cost_per_hour = st.number_input("Loaded cost ($/hour)", min_value=0.0, value=60.0, step=5.0)
        working_weeks = st.number_input("Working weeks/year", min_value=1, max_value=52, value=48, step=1)
        realization_pct = st.number_input("Benefit realization (%)", min_value=0.0, max_value=100.0, value=80.0, step=5.0)
        realization = float(realization_pct) / 100.0

    st.divider()
    discount_rate_pct = st.number_input("Discount rate (NPV, %)", min_value=0.0, value=10.0, step=1.0)
    discount_rate = float(discount_rate_pct) / 100.0


df = build_plan(float(year1_opex), float(year1_capex), float(annual_change_pct), years=5)

c1, c2 = st.columns([1.25, 1])
with c1:
    st.subheader("Cash flow table (Years 1–5)")
    st.dataframe(df, width="stretch", hide_index=True)

with c2:
    st.subheader("5‑year totals")
    total_opex = float(df["OpEx ($)"].sum())
    total_capex = float(df["CapEx ($)"].sum())
    total_cost = float(df["Total ($)"].sum())
    st.metric("OpEx (5‑yr)", fmt_money(total_opex))
    st.metric("CapEx (5‑yr)", fmt_money(total_capex))
    st.metric("Total cost / TCO (5‑yr)", fmt_money(total_cost))


st.subheader("Chart (x = $, y = year)")
chart_df = df.melt(id_vars=["Year"], value_vars=["OpEx ($)", "CapEx ($)", "Total ($)"], var_name="Type", value_name="Dollars")
chart_df["Year"] = chart_df["Year"].apply(lambda y: f"Year {y}")

fig = px.bar(
    chart_df,
    x="Dollars",
    y="Year",
    color="Type",
    orientation="h",
    barmode="group",
    height=420,
)
fig.update_layout(xaxis_title="Dollars ($)", yaxis_title="Year", legend_title_text="")
st.plotly_chart(fig, width="stretch")


def _benefits_series() -> np.ndarray:
    if benefit_mode == "Annual benefit ($)":
        bg = (1.0 + benefit_growth_pct / 100.0) ** np.arange(5, dtype=float)
        raw = float(annual_benefit) * bg
        return raw * realization

    annual = (
        float(team_size)
        * float(hours_saved_per_person_per_week)
        * float(working_weeks)
        * float(loaded_cost_per_hour)
    )
    return np.full(5, annual * realization, dtype=float)


benefits = _benefits_series()
costs = df["Total ($)"].to_numpy(dtype=float)
net = benefits - costs

roi_5yr = (float(benefits.sum()) - float(costs.sum())) / float(costs.sum()) if float(costs.sum()) > 0 else float("nan")

disc = (1.0 + discount_rate) ** np.arange(1, 6, dtype=float)
npv = float((net / disc).sum())

st.subheader("ROI (5 years)")
r1, r2, r3 = st.columns(3)
r1.metric("5‑yr benefits", fmt_money(float(benefits.sum())))
r2.metric("5‑yr net (benefits − costs)", fmt_money(float(net.sum())))
r3.metric("ROI (undiscounted)", "—" if not math.isfinite(roi_5yr) else f"{roi_5yr*100:,.1f}%")

st.caption(f"NPV (discount rate {discount_rate_pct:.0f}%): {fmt_money(npv)}")


with st.expander("Justified assumptions (paste into report)", expanded=True):
    st.markdown(
        """
**Cost assumptions (OpEx/CapEx)**
- **Year 1 OpEx** includes recurring costs such as subscriptions, support, and periodic training. In many projects, these are predictable and scale modestly with usage.
- **Year 1 CapEx** covers one-time setup/onboarding costs (initial configuration, initial hardware/software purchases, implementation effort).
- **Annual change (%)** models year-over-year drift from price increases, scaling usage, and incremental enhancements. A small positive rate (e.g., 3–8%) is commonly used when exact contracts are unknown.

**ROI assumptions (benefits)**
- The app separates **costs** (computed from OpEx/CapEx) from **benefits** (your assumptions), because benefits depend on the project context.
- **Benefit realization (%)** applies a conservative haircut so “time saved” is not over-claimed as cash value (not all saved time converts into measurable outcomes).
- The “Hours saved model” uses a **loaded labor rate** (salary + benefits + overhead) to convert time savings into dollar value, which is a standard internal-finance approach for knowledge work.

**NPV assumption**
- A discount rate (often 8–12% for internal projects) accounts for time value of money. If your course/project specifies a different rate, use that.
        """.strip()
    )


st.download_button(
    "Download table as CSV",
    data=df.to_csv(index=False),
    file_name="five_year_plan.csv",
    mime="text/csv",
    key="download_csv",
)
