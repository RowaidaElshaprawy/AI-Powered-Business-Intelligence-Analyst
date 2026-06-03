"""
Data loading, cleaning, SQL execution, and summarisation helpers.
"""
from __future__ import annotations
import re, sqlite3
from dataclasses import dataclass
import pandas as pd
from backend.config import TABLE_NAME


# ── dataframe normalisation ───────────────────────────────────────────────────

def clean_column_name(name: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z_]+", "_", name.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "column"


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names, parse date columns, coerce numerics."""
    out = df.copy()
    out.columns = [clean_column_name(c) for c in out.columns]
    for col in out.columns:
        if "date" in col:
            parsed = pd.to_datetime(out[col], errors="coerce")
            if parsed.notna().any():
                out[col] = parsed
        elif out[col].dtype == object:
            num = pd.to_numeric(out[col], errors="coerce")
            if num.notna().sum() > len(out) * 0.5:
                out[col] = num
    return out


# ── schema description ────────────────────────────────────────────────────────

def dataframe_schema(df: pd.DataFrame) -> str:
    lines = [f"Table: {TABLE_NAME}", "Columns:"]
    for col, dtype in df.dtypes.items():
        sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else "N/A"
        lines.append(f"  {col}: {dtype}  (e.g. {sample})")
    lines.append(f"Total rows: {len(df):,}")
    return "\n".join(lines)


# ── SQL execution ─────────────────────────────────────────────────────────────

def sanitize_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(";")
    forbidden = ["drop", "delete", "update", "insert", "alter", "truncate", "create"]
    for word in forbidden:
        if re.search(rf"\b{word}\b", cleaned, re.IGNORECASE):
            raise ValueError(f"Forbidden SQL keyword detected: {word}")
    return cleaned


def execute_sql_on_dataframe(df: pd.DataFrame, sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(":memory:")
    df.to_sql(TABLE_NAME, conn, index=False, if_exists="replace")
    try:
        result = pd.read_sql_query(sanitize_sql(sql), conn)
    finally:
        conn.close()
    return result


# ── KPI summary ───────────────────────────────────────────────────────────────

@dataclass
class AnalysisSummary:
    total_revenue: float
    total_profit:  float
    profit_margin: float
    rows_returned: int
    top_dimension: str
    weak_dimension: str

    def __str__(self) -> str:
        return (
            f"Rows: {self.rows_returned} | "
            f"Revenue: ${self.total_revenue:,.0f} | "
            f"Profit: ${self.total_profit:,.0f} | "
            f"Margin: {self.profit_margin*100:.1f}% | "
            f"Top: {self.top_dimension} | Weak: {self.weak_dimension}"
        )


def summarize_result(result_df: pd.DataFrame, source_df: pd.DataFrame | None = None) -> AnalysisSummary:
    rev_col  = next((c for c in result_df.columns if "revenue" in c.lower()), None)
    prof_col = next((c for c in result_df.columns if "profit"  in c.lower()), None)
    dim_cols = [c for c in result_df.columns if c not in [rev_col, prof_col] and result_df[c].dtype == object]
    dim      = dim_cols[-1] if dim_cols else (result_df.columns[0] if len(result_df.columns) else "")

    total_rev  = float(result_df[rev_col].sum())  if rev_col  else 0.0
    total_prof = float(result_df[prof_col].sum()) if prof_col else 0.0

    if source_df is not None:
        src_rev  = float(pd.to_numeric(source_df.get("revenue",  pd.Series()), errors="coerce").sum())
        src_prof = float(pd.to_numeric(source_df.get("profit",   pd.Series()), errors="coerce").sum())
        if total_rev  == 0: total_rev  = src_rev
        if total_prof == 0: total_prof = src_prof

    margin = total_prof / total_rev if total_rev else 0.0
    top, weak = "n/a", "n/a"
    if rev_col and dim in result_df.columns and not result_df.empty:
        grp = result_df.groupby(dim, dropna=False)[rev_col].sum().sort_values()
        if not grp.empty:
            weak = str(grp.index[0])
            top  = str(grp.index[-1])

    return AnalysisSummary(
        total_revenue=total_rev,
        total_profit=total_prof,
        profit_margin=margin,
        rows_returned=len(result_df),
        top_dimension=top,
        weak_dimension=weak,
    )
