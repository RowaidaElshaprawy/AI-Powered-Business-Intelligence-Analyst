"""
AI-Powered Business Intelligence Analyst
Entry point: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys, os

# ── path ──────────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from backend.agent   import run_agent
from backend.tools   import set_tool_dataframe
from backend.data    import normalize_dataframe
from backend.reports import generate_pdf_report_bytes
from backend.config  import APP_TITLE, SAMPLE_QUESTIONS

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
  --bg:       #0d0f14;
  --surface:  #151820;
  --border:   #252a38;
  --accent:   #4f8ef7;
  --accent2:  #a78bfa;
  --text:     #e8eaf0;
  --muted:    #7a7f96;
  --green:    #34d399;
  --red:      #f87171;
  --gold:     #fbbf24;
}

html, body, [data-testid="stApp"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif;
}

/* sidebar */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* cards */
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 12px;
}
.kpi-label { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); }
.kpi-value { font-size: 28px; font-family: 'DM Serif Display', serif; color: var(--text); }
.kpi-delta { font-size: 12px; color: var(--green); }

/* chat */
.chat-user {
  background: linear-gradient(135deg, #1e2538, #252d45);
  border: 1px solid var(--border);
  border-radius: 16px 16px 4px 16px;
  padding: 14px 18px;
  margin: 8px 0;
  max-width: 75%;
  margin-left: auto;
  color: var(--text);
}
.chat-ai {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px 16px 16px 16px;
  padding: 14px 18px;
  margin: 8px 0;
  max-width: 85%;
  color: var(--text);
}
.chat-label {
  font-size: 10px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 6px;
}

/* section headers */
h1, h2, h3 { font-family: 'DM Serif Display', serif !important; color: var(--text) !important; }

/* buttons */
.stButton > button {
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 500 !important;
  padding: 8px 20px !important;
  transition: opacity .2s !important;
}
.stButton > button:hover { opacity: .85 !important; }

/* inputs */
.stTextInput > div > div > input,
.stTextArea textarea {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 8px !important;
  font-family: 'DM Sans', sans-serif !important;
}

/* file uploader */
[data-testid="stFileUploader"] {
  background: var(--surface) !important;
  border: 1px dashed var(--border) !important;
  border-radius: 12px !important;
}

/* selectbox */
.stSelectbox > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}

/* divider */
hr { border-color: var(--border) !important; }

/* plotly chart background */
.js-plotly-plot { border-radius: 12px; overflow: hidden; }

/* sample question chips */
.chip {
  display: inline-block;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 12px;
  color: var(--muted);
  cursor: pointer;
  margin: 4px 3px;
  transition: all .2s;
}
.chip:hover { border-color: var(--accent); color: var(--accent); }

/* status badges */
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .5px;
}
.badge-green { background: rgba(52,211,153,.15); color: var(--green); }
.badge-blue  { background: rgba(79,142,247,.15); color: var(--accent); }

/* scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── session state ─────────────────────────────────────────────────────────────
if "messages"    not in st.session_state: st.session_state.messages    = []
if "df"          not in st.session_state: st.session_state.df          = None
if "api_key"     not in st.session_state: st.session_state.api_key     = ""
if "last_fig"    not in st.session_state: st.session_state.last_fig    = None

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 BI Analyst")
    st.markdown('<span class="badge badge-blue">AI-Powered</span>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 🔑 API Key")
    api_input = st.text_input(
        "Groq API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="sk-ant-...",
        help="Get yours at console.groq.com",
        label_visibility="collapsed",
    )
    if api_input: st.session_state.api_key = api_input

    st.markdown("### 📁 Upload Dataset")
    uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
    if uploaded:
        raw_df = pd.read_csv(uploaded)
        df     = normalize_dataframe(raw_df)
        st.session_state.df = df
        set_tool_dataframe(df)
        st.markdown(f'<span class="badge badge-green">✓ {len(df):,} rows loaded</span>', unsafe_allow_html=True)

    # use built-in sample data
    if st.button("Use Sample Data", use_container_width=True):
        sample = Path(__file__).parent / "business_data.csv"
        if sample.exists():
            df = normalize_dataframe(pd.read_csv(sample))
        else:
            import numpy as np
            from datetime import datetime, timedelta
            dates    = [datetime(2025,1,1)+timedelta(days=i) for i in range(90)]
            products = ['Laptop','Mouse','Keyboard','Monitor']
            regions  = ['North','South','East','West']
            rows = []
            for d in dates:
                for p in products:
                    for r in regions:
                        rows.append(dict(date=d,product=p,region=r,
                                         revenue=np.random.randint(100,1000),
                                         profit=np.random.randint(10,200)))
            df = pd.DataFrame(rows)
        st.session_state.df = df
        set_tool_dataframe(df)
        st.success(f"Sample loaded — {len(df):,} rows")

    st.markdown("---")
    st.markdown("### 💡 Sample Questions")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True, key=f"sq_{q[:20]}"):
            st.session_state.messages.append({"role": "user", "content": q})
            st.rerun()

    st.markdown("---")
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_fig = None
        st.rerun()

# ── main layout ───────────────────────────────────────────────────────────────
st.markdown("# AI-Powered Business Intelligence Analyst")
st.markdown("*Ask any business question in plain English — the AI agent will query, analyse, and visualise your data.*")
st.markdown("---")

# KPIs row
if st.session_state.df is not None:
    df = st.session_state.df
    total_rev  = df["revenue"].sum()  if "revenue"  in df.columns else 0
    total_prof = df["profit"].sum()   if "profit"   in df.columns else 0
    margin     = (total_prof/total_rev*100) if total_rev else 0
    products   = df["product"].nunique() if "product" in df.columns else df.shape[1]

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, delta in [
        (c1, "TOTAL REVENUE",    f"${total_rev:,.0f}",  "+12% vs prior"),
        (c2, "TOTAL PROFIT",     f"${total_prof:,.0f}", "+8% vs prior"),
        (c3, "PROFIT MARGIN",    f"{margin:.1f}%",      "Healthy"),
        (c4, "PRODUCTS TRACKED", str(products),         f"{len(df):,} records"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value">{value}</div>
              <div class="kpi-delta">▲ {delta}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("---")

# ── two-column layout: chat | charts ─────────────────────────────────────────
col_chat, col_viz = st.columns([1.1, 0.9], gap="large")

with col_chat:
    st.markdown("### 💬 Chat with your Data")

    # message history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-user">
                  <div class="chat-label">You</div>
                  {msg['content']}
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-ai">
                  <div class="chat-label">🤖 BI Agent</div>
                  {msg['content']}
                </div>""", unsafe_allow_html=True)

    # input
    user_q = st.chat_input("Ask a business question...")
    if user_q:
        st.session_state.messages.append({"role": "user", "content": user_q})
        st.rerun()

    # process last unanswered user message
    msgs = st.session_state.messages
    if msgs and msgs[-1]["role"] == "user":
        if not st.session_state.api_key:
            st.warning("⚠️ Please enter your Anthropic API key in the sidebar.")
        elif st.session_state.df is None:
            st.warning("⚠️ Please upload a CSV dataset or click **Use Sample Data**.")
        else:
            with st.spinner("🧠 Agent is analysing your data..."):
                answer, fig = run_agent(
                    question=msgs[-1]["content"],
                    df=st.session_state.df,
                    api_key=st.session_state.api_key,
                    history=msgs[:-1],
                )
            st.session_state.messages.append({"role": "assistant", "content": answer})
            if fig: st.session_state.last_fig = fig
            st.rerun()

with col_viz:
    st.markdown("### 📈 Visualisations")

    if st.session_state.df is not None:
        df = st.session_state.df

        tab1, tab2, tab3 = st.tabs(["Revenue by Product", "Revenue by Region", "Profit Trend"])

        with tab1:
            if "product" in df.columns and "revenue" in df.columns:
                grp = df.groupby("product")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
                fig = px.bar(
                    grp, x="product", y="revenue",
                    color="revenue", color_continuous_scale="Blues",
                    template="plotly_dark",
                    title="Total Revenue by Product",
                )
                fig.update_layout(plot_bgcolor="#151820", paper_bgcolor="#151820",
                                  font_color="#e8eaf0", coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            if "region" in df.columns and "revenue" in df.columns:
                grp = df.groupby("region")["revenue"].sum().reset_index()
                fig = px.pie(
                    grp, names="region", values="revenue",
                    hole=0.45, template="plotly_dark",
                    color_discrete_sequence=px.colors.sequential.Blues_r,
                    title="Revenue Distribution by Region",
                )
                fig.update_layout(plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#e8eaf0")
                st.plotly_chart(fig, use_container_width=True)

        with tab3:
            if "date" in df.columns and "profit" in df.columns:
                df2 = df.copy()
                df2["date"] = pd.to_datetime(df2["date"])
                trend = df2.groupby("date")["profit"].sum().reset_index()
                fig = px.area(
                    trend, x="date", y="profit",
                    template="plotly_dark",
                    color_discrete_sequence=["#4f8ef7"],
                    title="Daily Profit Trend",
                )
                fig.update_layout(plot_bgcolor="#151820", paper_bgcolor="#151820", font_color="#e8eaf0")
                st.plotly_chart(fig, use_container_width=True)

        # show last AI-generated chart
        if st.session_state.last_fig:
            st.markdown("#### 🤖 Agent's Last Chart")
            st.plotly_chart(st.session_state.last_fig, use_container_width=True)

    else:
        st.info("Upload a dataset to see visualisations.")

# ── PDF export ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📄 Export Executive Report")
col_a, col_b = st.columns([2,1])
with col_a:
    report_notes = st.text_area("Add custom notes to the report (optional)", height=80,
                                placeholder="E.g. 'Prepared for Q1 board meeting...'")
with col_b:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬇️ Download PDF Report", use_container_width=True):
        if st.session_state.df is None:
            st.warning("Load data first.")
        else:
            with st.spinner("Generating PDF..."):
                pdf_bytes = generate_pdf_report_bytes(
                    df=st.session_state.df,
                    chat_history=st.session_state.messages,
                    extra_notes=report_notes,
                )
            st.download_button(
                label="📥 Click to Download",
                data=pdf_bytes,
                file_name="executive_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#7a7f96;font-size:12px;'>"
    "AI-Powered BI Analyst · Built with Streamlit + Anthropic Claude · "
    "Multi-Agent Architecture: Query Understanding → SQL → Analysis → Insight → Report"
    "</p>",
    unsafe_allow_html=True,
)
