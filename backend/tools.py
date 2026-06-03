"""
LangChain @tool functions for the LangGraph agent.
Tools are decorated with @tool so LangGraph / LangChain can bind them directly.
A plain dispatcher is also kept for any direct calls.
"""
from __future__ import annotations
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from langchain_core.tools import tool

from backend.data     import execute_sql_on_dataframe, summarize_result, dataframe_schema
from backend.analysis import build_analysis_plan

# ── shared state ──────────────────────────────────────────────────────────────
_shared_df: pd.DataFrame | None = None
_last_fig:  go.Figure   | None  = None

def set_tool_dataframe(df: pd.DataFrame) -> None:
    global _shared_df
    _shared_df = df

def get_tool_dataframe() -> pd.DataFrame | None:
    return _shared_df

def set_last_fig(fig: go.Figure | None) -> None:
    global _last_fig
    _last_fig = fig

def get_last_fig() -> go.Figure | None:
    return _last_fig


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 1 — inspect schema
# ══════════════════════════════════════════════════════════════════════════════
@tool
def inspect_dataset_schema() -> str:
    """Inspect column names, data types, and sample rows of the loaded dataset.
    Call this first if unsure about available columns."""
    if _shared_df is None:
        return "Error: No dataset loaded. Please upload a CSV file first."
    return dataframe_schema(_shared_df)


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 2 — analyse data + generate chart
# ══════════════════════════════════════════════════════════════════════════════
@tool
def analyze_business_data(
    metric:     str = "revenue",
    group_by:   str = "product",
    date_grain: str = "",
    chart_type: str = "",
    filter_sql: str = "",
) -> str:
    """Perform statistical analysis on the dataset.
    Returns revenue/profit totals, top/weak performers, and generates a Plotly chart.
    ALWAYS call this before answering any numeric business question.

    Args:
        metric:     Column to aggregate — e.g. 'revenue' or 'profit'. Default: 'revenue'.
        group_by:   Column to group by  — e.g. 'product', 'region', 'date'. Default: 'product'.
        date_grain: Time granularity when grouping by date: 'monthly', 'weekly', 'daily'.
        chart_type: Hint for chart style: 'bar', 'line', 'pie', 'scatter'. Auto-inferred if empty.
        filter_sql: Optional HAVING clause, e.g. 'SUM(revenue) > 50000'.
    """
    if _shared_df is None:
        return json.dumps({"error": "No dataset loaded."})

    plan = build_analysis_plan(
        question="",
        df=_shared_df,
        group_by=group_by,
        metric=metric,
        date_grain=date_grain,
        chart_type=chart_type,
    )
    sql = plan["sql"]
    if filter_sql:
        sql += f" HAVING {filter_sql}"

    try:
        result_df = execute_sql_on_dataframe(_shared_df, sql)
    except Exception as e:
        return json.dumps({"error": str(e), "sql": sql})

    summary = summarize_result(result_df, _shared_df)

    # build chart
    ct   = plan["chart_type"]
    x, y = plan["chart_x"], plan["chart_y"]
    kw   = dict(
        template="plotly_dark",
        title=f"{metric.title()} by {group_by.title()}",
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    try:
        if ct == "line":
            fig = px.line(result_df, x=x, y=y, **kw)
        elif ct == "pie":
            fig = px.pie(result_df, names=x, values=y, hole=0.4, **kw)
        elif ct == "scatter":
            fig = px.scatter(result_df, x=x, y=y, **kw)
        else:
            fig = px.bar(result_df, x=x, y=y, color=y,
                         color_continuous_scale="Blues", **kw)
        fig.update_layout(plot_bgcolor="#151820", paper_bgcolor="#151820",
                          font_color="#e8eaf0")
        set_last_fig(fig)
    except Exception:
        pass

    result = {
        "summary":        str(summary),
        "rows_returned":  summary.rows_returned,
        "total_revenue":  summary.total_revenue,
        "total_profit":   summary.total_profit,
        "profit_margin":  round(summary.profit_margin * 100, 2),
        "top_performer":  summary.top_dimension,
        "weak_performer": summary.weak_dimension,
        "data_preview":   result_df.head(10).to_string(index=False),
        "sql_used":       sql,
    }
    return json.dumps(result, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 3 — PDF report trigger
# ══════════════════════════════════════════════════════════════════════════════
@tool
def generate_pdf_report(content: str) -> str:
    """Compile analysis findings into a downloadable executive PDF report.

    Args:
        content: The full narrative text to include in the report.
    """
    return "PDF_REQUESTED:" + content


# ── convenience list for LangChain tool binding ───────────────────────────────
ALL_TOOLS = [inspect_dataset_schema, analyze_business_data, generate_pdf_report]
