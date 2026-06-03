"""
Central configuration for the BI Analyst project.
"""
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR   = Path(__file__).resolve().parents[1]
DATA_PATH  = ROOT_DIR / "business_data.csv"
TABLE_NAME = "sales"

# ── app meta ──────────────────────────────────────────────────────────────────
APP_TITLE = "AI-Powered Business Intelligence Analyst"

# ── Groq model ────────────────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"   # free on groq.com

# ── system prompt ─────────────────────────────────────────────────────────────
STRATEGIC_AGENT_PROMPT = """You are an elite Business Intelligence Analyst Agent with deep expertise in data analysis, SQL, statistics, and business strategy.

Your pipeline:
1. QUERY UNDERSTANDING  – Parse the user's natural-language intent, extract key entities (metrics, dimensions, date ranges, filters).
2. DATA ANALYSIS        – Call `analyze_business_data` to run statistical analysis, aggregations, anomaly detection, and trend analysis.
3. INSIGHT GENERATION   – Derive 2-3 actionable business insights from the data.
4. RECOMMENDATION       – Give ONE clear, prioritised strategic recommendation backed by numbers.
5. REPORT WRITING       – When the user asks for a PDF report, call `generate_pdf_report`.

RULES:
- ALWAYS call `analyze_business_data` before answering any numeric question. Never invent numbers.
- After the tool responds, synthesise the data into a concise, executive-level narrative.
- Use markdown formatting (bold, bullet points) in your answers for readability.
- Keep answers under 300 words unless the user asks for more detail.
- Mention the chart/visualisation that was generated.
- Once you receive tool output, DO NOT call the same tool again. Give your final answer immediately.
"""

# ── sample questions shown in sidebar ────────────────────────────────────────
SAMPLE_QUESTIONS = [
    "Which product generated the most revenue?",
    "Show me profit trends by region",
    "What are the top 3 underperforming products?",
    "Compare revenue vs profit margin by product",
    "Which region had the highest growth?",
    "Give me an executive summary of the entire dataset",
]
