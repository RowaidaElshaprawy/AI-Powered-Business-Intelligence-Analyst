from pathlib import Path

ROOT_DIR   = Path(__file__).resolve().parents[1]
DATA_PATH  = ROOT_DIR / "business_data.csv"
TABLE_NAME = "sales"
APP_TITLE  = "AI-Powered Business Intelligence Analyst"

STRATEGIC_AGENT_PROMPT = """You are a Business Intelligence Analyst Agent.

To answer any business question, you MUST call the analyze_business_data tool first.

Tool usage rules:
- metric must be exactly "revenue" or "profit" (one word only, never both)
- group_by must be exactly "product" or "region" or "date"
- Call the tool ONCE, then give your final answer based on the result.
- Never invent numbers. Always use the tool output.

After getting tool results, give a concise insight with bullet points.
"""

SAMPLE_QUESTIONS = [
    "Which product generated the most revenue?",
    "Show me profit by region",
    "Which product has the lowest revenue?",
    "Compare profit by product",
    "Which region had the highest revenue?",
    "Give me an executive summary of the dataset",
]