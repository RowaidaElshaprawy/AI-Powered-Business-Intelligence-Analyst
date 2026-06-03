"""
Multi-agent loop: plain Groq SDK, simplified tools, no LangChain binding.
"""
from __future__ import annotations
import json
import plotly.graph_objects as go
import pandas as pd
from groq import Groq

from backend.config import STRATEGIC_AGENT_PROMPT
from backend.tools  import set_tool_dataframe, get_last_fig
from backend.tools  import inspect_dataset_schema, analyze_business_data, generate_pdf_report

GROQ_MODEL = "llama-3.3-70b-versatile"

# ── MINIMAL tool schemas — fewer params = fewer hallucinations ────────────────
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "inspect_dataset_schema",
            "description": "Get column names and data types of the dataset.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_business_data",
            "description": "Analyze the dataset. Call this for any business question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric":   {"type": "string", "description": "revenue or profit"},
                    "group_by": {"type": "string", "description": "product or region or date"},
                },
                "required": ["metric", "group_by"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_pdf_report",
            "description": "Generate a PDF report with the findings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Report text"},
                },
                "required": ["content"],
            },
        },
    },
]


def _dispatch(name: str, args: dict) -> str:
    if name == "inspect_dataset_schema":
        return inspect_dataset_schema.invoke({})
    if name == "analyze_business_data":
        return analyze_business_data.invoke(args)
    if name == "generate_pdf_report":
        return generate_pdf_report.invoke(args)
    return f"Unknown tool: {name}"


def run_agent(
    question: str,
    df: pd.DataFrame,
    api_key: str,
    history: list[dict] | None = None,
    **_,
) -> tuple[str, go.Figure | None]:
    set_tool_dataframe(df)
    client = Groq(api_key=api_key)

    messages = [{"role": "system", "content": STRATEGIC_AGENT_PROMPT}]
    for m in (history or []):
        if m["role"] in ("user", "assistant"):
            messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": question})

    for _ in range(8):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            max_tokens=2048,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or "Analysis complete.", get_last_fig()

        # append assistant turn
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        })

        # execute tools
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}
            result = _dispatch(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return "Reached max steps. Please try a more specific question.", get_last_fig()