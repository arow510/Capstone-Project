# Streamlit: 5-Year OpEx/CapEx + ROI Simulator

This Streamlit web app estimates **OpEx, CapEx, and ROI** for the next **5 years**, with:

- **Manual inputs (costs)**: 1st year OpEx ($), 1st year CapEx ($), annual change (%)
- **Outputs**: one cash-flow table + one chart (**x = $**, **y = year**)
- **ROI**: editable benefit assumptions + optional NPV

## Local run (Python 3.9+)

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

If port 8501 is busy:

```bash
python -m streamlit run app.py --server.port 8503
```

## Azure App Service (Linux, Python 3.10)

- **Runtime stack**: Linux, Python 3.10
- **Startup command**:

```bash
streamlit run app.py --server.port=8000 --server.address=0.0.0.0
```

## Model assumptions (how to justify in your report)

- **OpEx**: recurring costs (subscriptions, support, training refreshers). Typically scales slowly with usage.
- **CapEx**: one-time enablement/setup (initial implementation effort, initial devices/software).
- **Annual change (%)**: captures price drift + scaling over time. When exact contracts are unknown, a modest rate (e.g., 3–8%) is defensible.
- **ROI benefits**: depend on your project; the app lets you use either:
  - **Annual benefit ($)** (with optional benefit growth), or
  - **Hours-saved model** (team size × hours saved × loaded $/hr × realization %)
- **Benefit realization (%)**: a conservative haircut so you don’t over-claim “time saved” as real dollars.
- **NPV discount rate**: often 8–12% for internal projects; use your course’s required rate if specified.
