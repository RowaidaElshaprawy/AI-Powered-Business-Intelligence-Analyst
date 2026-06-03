"""
Chart-type inference and analysis plan building.
"""
from __future__ import annotations
import pandas as pd
from backend.config import TABLE_NAME


def infer_chart_type(question: str, user_hint: str = "") -> str:
    if user_hint:
        return user_hint
    q = question.lower()
    if any(x in q for x in ["trend", "over time", "monthly", "daily", "weekly", "timeline"]):
        return "line"
    if any(x in q for x in ["distribution", "share", "breakdown", "percentage", "%"]):
        return "pie"
    if any(x in q for x in ["scatter", "correlation", "vs", "versus"]):
        return "scatter"
    return "bar"


def build_analysis_plan(
    question: str,
    df: pd.DataFrame,
    group_by:   str = "",
    metric:     str = "",
    date_grain: str = "",
    chart_type: str = "",
) -> dict:
    metric   = metric   if metric   else "revenue"
    group_by = group_by if group_by else "product"

    # map requested column to actual column name
    actual_group  = next((c for c in df.columns if group_by.lower() in c.lower()), df.columns[0])
    actual_metric = next((c for c in df.columns if metric.lower()  in c.lower()), None)
    if actual_metric is None:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        actual_metric = num_cols[0] if num_cols else df.columns[-1]

    if date_grain and "date" in df.columns:
        sql = (
            f"SELECT strftime('%Y-%m', date) AS period, {actual_group}, "
            f"SUM({actual_metric}) AS {actual_metric} "
            f"FROM {TABLE_NAME} "
            f"GROUP BY period, {actual_group} "
            f"ORDER BY period"
        )
    else:
        sql = (
            f"SELECT {actual_group}, SUM({actual_metric}) AS {actual_metric} "
            f"FROM {TABLE_NAME} "
            f"GROUP BY {actual_group} "
            f"ORDER BY {actual_metric} DESC"
        )

    return {
        "intent":     f"Analysing {metric} by {group_by}",
        "sql":        sql,
        "chart_type": infer_chart_type(question, chart_type),
        "chart_x":    actual_group,
        "chart_y":    actual_metric,
        "chart_color": actual_group if infer_chart_type(question, chart_type) == "bar" else None,
    }
