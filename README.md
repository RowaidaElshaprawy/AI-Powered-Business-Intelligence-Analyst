# 📊 AI-Powered Business Intelligence Analyst

A production-grade multi-agent BI system that lets business stakeholders ask data questions in plain English and get instant insights, charts, and PDF reports 

---

## 🏗 Architecture

```
User Question (natural language)
        │
        ▼
┌─────────────────────────────────────────┐
│           BI Agent            
│  1. Query Understanding                 │
│  2. SQL Generator  ──► SQLite in-memory │
│  3. Data Analyst   ──► Pandas + SciPy   │
│  4. Visualisation  ──► Plotly           │
│  5. Insight Generator                   │
│  6. Report Writer  ──► ReportLab PDF    │
└─────────────────────────────────────────┘
        │
        ▼
  Streamlit UI (charts + chat + PDF export)
```

## 📁 Project Structure

```
bi_analyst/
├── app.py                  ← Streamlit entry point
├── create_data.py          ← Generate sample CSV
├── business_data.csv       ← Sample dataset (auto-generated)
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml         ← Dark theme config
└── backend/
    ├── __init__.py
    ├── agent.py            ← Agentic loop (Anthropic tool-use)
    ├── analysis.py         ← Chart-type inference + SQL plan
    ├── config.py           ← Prompts, paths, model name
    ├── data.py             ← Data normalisation + SQL execution
    ├── reports.py          ← ReportLab PDF generator
    └── tools.py            ← Tool schemas + dispatcher
```

---

## 🚀 Setup & Deploy (VS Code + GitHub)

### Prerequisites
- Python 3.10 or higher
- Git installed
- VS Code installed
- A free Groq api key

---

### Step 1 — Clone / Open in VS Code

```bash
# If you already have the folder:
code bi_analyst

# OR clone from GitHub after pushing (see Step 5):
git clone https://github.com/YOUR_USERNAME/bi-analyst.git
cd bi-analyst
code .
```

---

### Step 2 — Create a Virtual Environment

Open the VS Code **Terminal** (`Ctrl+`` ` or `Terminal → New Terminal`) and run:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

VS Code will detect the venv. When prompted **"Select Interpreter"**, choose `.venv`.

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: `Groq`, `streamlit`, `pandas`, `plotly`, `reportlab`, `fpdf2`, `scipy`, `statsmodels`, `kaleido`.

---

### Step 4 — Generate Sample Data (optional)

```bash
python create_data.py
```

This creates `business_data.csv` — 1,440 rows of sales data across 4 products, 4 regions, 90 days.

---

### Step 5 — Run the App Locally

```bash
streamlit run app.py
```

The browser opens automatically at `http://localhost:8501`.

**In the sidebar:**
1. Paste your Groq API key
2. Click **Use Sample Data** (or upload your own CSV)
3. Ask a question, e.g. *"Which product generated the most revenue?"*

---

### Step 6 — Push to GitHub

```bash
# Inside the bi_analyst folder:
git init
git add .
git commit -m "Initial commit — AI BI Analyst"

# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/bi-analyst.git
git branch -M main
git push -u origin main
```

---

### Step 7 — Deploy to Streamlit Cloud (free)

1. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Connect your GitHub account
3. Select repo `bi-analyst`, branch `main`, main file `app.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   Groq_API_KEY = "sk-ant-..."
   ```
5. Click **Deploy** — live URL in ~2 minutes ✅


---

## ⚙️ Configuration

Edit `backend/config.py` to:
- Change the Claude model (`claude-haiku-4-5-20251001` for speed/cost, `claude-opus-4-5` for quality)
- Edit the system prompt to specialise for your industry
- Add/remove sample questions in the sidebar

---

## 🔒 Security Notes

- Never commit `.env` or `secrets.toml` to Git (both are in `.gitignore`)
- The SQL layer rejects `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`
- API key is only held in `st.session_state` for the browser session

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit + custom CSS |
| Charts | Plotly Express |
| Agent Framework | Anthropic tool-use (native) |
| LLM | Claude claude-opus-4-5 |
| Data Analysis | Pandas + SciPy + NumPy |
| SQL Engine | SQLite (in-memory) |
| PDF Export | ReportLab |
| Stats | Statsmodels |
