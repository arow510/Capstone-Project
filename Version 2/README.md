# Version 2: 5-Year OpEx/CapEx + ROI (Tangible + Intangible)

This Streamlit app simulates a 5-year cost plan and ROI.

## What’s included in v2

1. Existing outputs kept:
   - 1 cash-flow table (OpEx, CapEx, Total cost) for Years 1–5
   - 1 chart with **x = dollars** and **y = year**
   - ROI summary metrics + a “Justified assumptions” section for your report
2. New v2 additions:
   - A **table of tangible vs. intangible returns** (Years 1–5)
   - A **new ROI chart** where **x = ROI %** and **y = year**

## Local run

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

## Azure App Service (Linux, Python 3.10)

- **Startup command** (set exactly):

```bash
streamlit run app.py --server.port=8000 --server.address=0.0.0.0
```

If you deploy from this `Version 2` folder as the application root, the command above works as-is.

