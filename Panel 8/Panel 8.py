"""
Panel 8 — Adoption Curve (Capstone integration)
Run from repo root:
  streamlit run "Panel 8/Panel 8.py"
Or:
  cd "Panel 8"
  streamlit run "Panel 8.py"
"""

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Panel 8: Adoption Curve", layout="wide")


def _clamp_float(x: float, lo: float, hi: float) -> float:
    if not math.isfinite(x):
        return lo
    return max(lo, min(hi, x))


def simulate_adoption(
    training_h: float,
    leadership_pct: float,
    months: int,
) -> pd.DataFrame:
    """
    Simple interpretable model:
    - Adoption follows a logistic (S-curve) toward a ceiling driven by training + leadership.
    - Resistance index decays over time; stronger programs accelerate decay.
    """
    t = np.arange(0, months + 1, dtype=float)

    # Ceiling adoption % (not everyone adopts even with max inputs)
    adoption_ceiling = _clamp_float(35.0 + 0.9 * training_h + 0.22 * leadership_pct, 5.0, 95.0)

    # Steeper / earlier lift with more training & engaged leadership
    k = _clamp_float(0.12 + 0.0035 * training_h + 0.0018 * leadership_pct, 0.05, 0.55)
    t0 = _clamp_float(10.0 - 0.12 * training_h - 0.06 * leadership_pct, 2.0, 18.0)

    adoption_pct = adoption_ceiling / (1.0 + np.exp(-k * (t - t0)))

    # Resistance: high baseline when investment is low; falls faster with good programs
    r0 = _clamp_float(88.0 - 0.55 * training_h - 0.22 * leadership_pct, 18.0, 100.0)
    decay = _clamp_float(0.055 + 0.0018 * training_h + 0.0010 * leadership_pct, 0.02, 0.35)
    resistance = r0 * np.exp(-decay * t)

    # Keep resistance on 0–100 index scale; optionally soft-couple to adoption (optional refinement)
    resistance = np.clip(resistance, 0.0, 100.0)

    return pd.DataFrame(
        {
            "Month": t.astype(int),
            "Adoption %": np.round(adoption_pct, 2),
            "Resistance index": np.round(resistance, 2),
        }
    )


st.title("Panel 8 — Adoption curve")
st.caption(
    "Simulate employee **adoption rate** over time from **training hours** and **leadership engagement**. "
    "Includes a **resistance index** line for change-management narrative."
)

with st.sidebar:
    st.subheader("Panel 8 inputs")
    training_h = st.slider("Training (hours / employee / year)", min_value=0.0, max_value=40.0, value=16.0, step=1.0)
    leadership_pct = st.slider("Leadership engagement (%)", min_value=0.0, max_value=100.0, value=55.0, step=5.0)
    horizon_m = st.slider("Horizon (months)", min_value=6, max_value=36, value=24, step=1)

df = simulate_adoption(float(training_h), float(leadership_pct), int(horizon_m))

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df["Month"],
        y=df["Adoption %"],
        mode="lines",
        name="Adoption %",
        line=dict(color="#2ecc71", width=3),
    )
)
fig.add_trace(
    go.Scatter(
        x=df["Month"],
        y=df["Resistance index"],
        mode="lines",
        name="Resistance index",
        line=dict(color="#e74c3c", width=2, dash="dash"),
        yaxis="y2",
    )
)
fig.update_layout(
    height=480,
    xaxis_title="Time (months)",
    yaxis=dict(title="Adoption %", range=[0, 100], side="left"),
    yaxis2=dict(title="Resistance index (0–100)", overlaying="y", side="right", range=[0, 100], showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=60, r=60, t=40, b=60),
)
st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("Latest month snapshot")
    last = df.iloc[-1]
    st.metric("Adoption %", f"{last['Adoption %']:.1f}%")
    st.metric("Resistance index", f"{last['Resistance index']:.1f}")
with right:
    st.subheader("Table (Adoption vs resistance)")
    st.dataframe(df, width="stretch", hide_index=True)

st.download_button(
    "Download CSV",
    data=df.to_csv(index=False),
    file_name="panel8_adoption_curve.csv",
    mime="text/csv",
    key="panel8_csv",
)

with st.expander("How to explain this in your capstone (Panel 8)", expanded=False):
    st.markdown(
        """
- **Adoption %** uses a logistic (S-curve): change rarely jumps instantly; it ramps as behaviors spread.
- **Training hours** lift both the **ceiling** (how far adoption can go) and the **speed** toward that ceiling.
- **Leadership engagement %** models visible sponsorship, coaching, and accountability—accelerating uptake.
- **Resistance index** is a separate decaying curve: skepticism and friction fall faster when programs are stronger.
        """.strip()
    )
