from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from virtual_sales_agent.agents import (
    catalog_agent,
    catalog_tools,
    order_agent,
    order_safe_tools,
    order_sensitive_tools,
    recommendation_agent,
    recommendation_tools,
    route_catalog,
    route_from_supervisor,
    route_order,
    route_recommendation,
    route_support,
    supervisor_node,
    support_agent,
    support_tools,
)
from virtual_sales_agent.state import State
from virtual_sales_agent.utils import create_tool_node_with_fallback

# ─────────────────────────────────────────────────────────────────────────────
# GRAPH ASSEMBLY
# Each agent is defined in its own file under virtual_sales_agent/agents/.
# This file only wires the nodes and edges together.
#
# Flow:
#   START → supervisor → catalog_agent      → catalog_tools      → catalog_agent
#                      → recommendation_agent → recommendation_tools → recommendation_agent
#                      → order_agent          → order_safe_tools     → order_agent
#                                             → order_sensitive_tools (requires human approval)
#                      → support_agent        → support_tools        → support_agent
#                      → END
# ─────────────────────────────────────────────────────────────────────────────

builder = StateGraph(State)

# ── Nodes ────────────────────────────────────────────────────────────────────
builder.add_node("supervisor", supervisor_node)                                              # Agent 1
builder.add_node("catalog_agent", catalog_agent)                                             # Agent 2
builder.add_node("catalog_tools", create_tool_node_with_fallback(catalog_tools))
builder.add_node("recommendation_agent", recommendation_agent)                               # Agent 3
builder.add_node("recommendation_tools", create_tool_node_with_fallback(recommendation_tools))
builder.add_node("order_agent", order_agent)                                                 # Agent 4
builder.add_node("order_safe_tools", create_tool_node_with_fallback(order_safe_tools))
builder.add_node("order_sensitive_tools", create_tool_node_with_fallback(order_sensitive_tools))
builder.add_node("support_agent", support_agent)                                             # Agent 5
builder.add_node("support_tools", create_tool_node_with_fallback(support_tools))

# ── Supervisor routes to specialist agents ───────────────────────────────────
builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "catalog_agent": "catalog_agent",
        "recommendation_agent": "recommendation_agent",
        "order_agent": "order_agent",
        "support_agent": "support_agent",
        END: END,
    },
)

# ── Catalog agent loop ───────────────────────────────────────────────────────
builder.add_conditional_edges(
    "catalog_agent", route_catalog, {"catalog_tools": "catalog_tools", END: END}
)
builder.add_edge("catalog_tools", "catalog_agent")

# ── Recommendation agent loop ────────────────────────────────────────────────
builder.add_conditional_edges(
    "recommendation_agent",
    route_recommendation,
    {"recommendation_tools": "recommendation_tools", END: END},
)
builder.add_edge("recommendation_tools", "recommendation_agent")

# ── Order agent loop (sensitive tools pause for human approval) ───────────────
builder.add_conditional_edges(
    "order_agent",
    route_order,
    {
        "order_safe_tools": "order_safe_tools",
        "order_sensitive_tools": "order_sensitive_tools",
        END: END,
    },
)
builder.add_edge("order_safe_tools", "order_agent")
builder.add_edge("order_sensitive_tools", "order_agent")

# ── Support agent loop ───────────────────────────────────────────────────────
builder.add_conditional_edges(
    "support_agent", route_support, {"support_tools": "support_tools", END: END}
)
builder.add_edge("support_tools", "support_agent")

# ── Compile ──────────────────────────────────────────────────────────────────
memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["order_sensitive_tools"],
)
