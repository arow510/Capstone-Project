# Panel 8 — Adoption curve

Streamlit panel that simulates **employee adoption %** over time from **training hours** and **leadership engagement %**, plus a **resistance index** (0–100) that decays as programs strengthen. Charts and table are interactive; you can download the series as CSV.

## Requirements

- Python 3.9+ recommended

## Setup

From this folder:

```bash
pip install -r requirements.txt
```

From the repository root:

```bash
pip install -r "Panel 8/requirements.txt"
```

## Run locally

From the repository root:

```bash
streamlit run "Panel 8/Panel 8.py"
```

Or from this folder:

```bash
cd "Panel 8"
streamlit run "Panel 8.py"
```

If port 8501 is in use:

```bash
python -m streamlit run "Panel 8.py" --server.port 8503
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## What you can adjust

Sidebar controls:

- **Training (hours / employee / year)**
- **Leadership engagement (%)**
- **Horizon (months)**

The model uses a logistic (S-curve) toward an adoption ceiling influenced by those inputs; resistance follows a decaying curve for narrative around change management.

## Files

| File | Purpose |
|------|---------|
| `Panel 8.py` | Streamlit app |
| `requirements.txt` | Python dependencies |

## Hosting note

GitHub stores the code; to share a **public URL** without asking others to install Python, deploy with [Streamlit Community Cloud](https://streamlit.io/cloud) or another host, and point the entry file to `Panel 8/Panel 8.py` on the branch you use.
