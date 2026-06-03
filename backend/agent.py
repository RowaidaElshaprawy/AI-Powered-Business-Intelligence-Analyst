"""
Multi-turn agentic loop using Anthropic's tool-use API.

Agents modelled:
  1. Query Understanding  – handled by the system prompt
  2. SQL Generator        – handled by analyze_business_data tool
  3. Data Analyst         – tool + post-processing
  4. Visualisation Agent  – plotly fig returned alongside text
  5. Insight Generator    – in the final LLM response
  6. Report Writer        – generate_pdf_report tool
"""
from __future__ import annotations
import json
from groq import Groq
import plotly.graph_objects as go
import pandas as pd

from backend.config import STRATEGIC_AGENT_PROMPT, GROQ_MODEL
from backend.tools  import TOOL_SCHEMAS, dispatch_tool, get_last_fig

def run_agent(
    question:  str,
    df:        pd.DataFrame,
    api_key:   str,
    history:   list[dict] | None = None,
    max_turns: int = 8,
) -> tuple[str, go.Figure | None]:
    
    client = Groq(api_key=api_key)

    # Convert history to Groq/OpenAI format
    messages = [{"role": "system", "content": STRATEGIC_AGENT_PROMPT}]
    for m in (history or []):
        if m["role"] in ("user", "assistant", "tool"):
            messages.append({"role": m["role"], "content": m["content"]})
    
    messages.append({"role": "user", "content": question})

    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message)

        # If no tool calls → return final answer
        if not message.tool_calls:
            return message.content or "Analysis complete.", get_last_fig()

        # Execute tools
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            output = dispatch_tool(tool_name, tool_args)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(output)
            })

    return "Reached maximum reasoning steps.", get_last_fig()