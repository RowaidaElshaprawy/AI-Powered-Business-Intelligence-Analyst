"""
Multi-agent loop built with LangGraph + Groq (LLaMA 3.3 70B — free tier).

Graph topology:
  [entry] → agent_node ──(tool_calls?)──► tool_node → agent_node → ...
                      └──(no calls)────► END

Agents modelled inside the single graph:
  1. Query Understanding  – system prompt parses intent
  2. SQL Generator        – analyze_business_data tool builds + runs SQL
  3. Data Analyst         – tool returns stats & KPIs
  4. Visualisation Agent  – tool generates Plotly figure
  5. Insight Generator    – LLM synthesises findings into narrative
  6. Report Writer        – generate_pdf_report tool produces PDF
"""
from __future__ import annotations
from typing import TypedDict, Annotated, Sequence
import operator

import plotly.graph_objects as go
import pandas as pd

from langchain_groq          import ChatGroq
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph         import StateGraph, END
from langgraph.prebuilt      import ToolNode

from backend.config import STRATEGIC_AGENT_PROMPT, GROQ_MODEL
from backend.tools  import ALL_TOOLS, get_last_fig, set_tool_dataframe


# ── LangGraph state ───────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# ── graph factory ─────────────────────────────────────────────────────────────
def _build_graph(api_key: str):
    llm = ChatGroq(groq_api_key=api_key, model=GROQ_MODEL)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    sys_msg = SystemMessage(content=STRATEGIC_AGENT_PROMPT)

    def agent_node(state: AgentState):
        # strip any previous SystemMessages to avoid duplication, prepend ours
        msgs = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
        response = llm_with_tools.invoke([sys_msg] + msgs)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools=ALL_TOOLS))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")
    return graph.compile()


# ── public entry point ────────────────────────────────────────────────────────
def run_agent(
    question: str,
    df:       pd.DataFrame,
    api_key:  str,
    history:  list[dict] | None = None,
    **_,
) -> tuple[str, go.Figure | None]:
    """
    Run the LangGraph agent and return (answer_text, plotly_figure | None).
    """
    set_tool_dataframe(df)
    graph = _build_graph(api_key)

    # convert chat history to LangChain message objects
    lc_messages: list[BaseMessage] = []
    for m in (history or []):
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))
    lc_messages.append(HumanMessage(content=question))

    result = graph.invoke({"messages": lc_messages})

    # extract final text from the last AI message
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            return str(msg.content), get_last_fig()

    return "Analysis complete.", get_last_fig()
