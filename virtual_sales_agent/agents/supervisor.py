"""
Agent 1 — Supervisor
Reads the user's intent and routes to the correct specialist agent.
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END

from virtual_sales_agent.llm import llm
from virtual_sales_agent.state import State

_routing_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a routing supervisor for a virtual sales assistant system.
Read the conversation and the user's latest message, then output ONLY one word:

catalog     → user wants to browse, search, list, or discover products/categories
recommend   → user wants personalised product suggestions or recommendations
order       → user wants to place an order, check order status, or view order history
support     → user has a complaint, question about store policies, shipping, returns, or payment
finish      → the user's request has already been fully answered

Output ONLY the single word, nothing else.""",
        ),
        ("placeholder", "{messages}"),
    ]
)


def supervisor_node(state: State, config: RunnableConfig):
    """Agent 1: Supervisor — routes each user turn to the right specialist."""
    configuration = config.get("configurable", {})
    customer_id = configuration.get("customer_id", None)
    chain = _routing_prompt | llm
    result = chain.invoke({**state, "user_info": customer_id})
    # Handle result.content being either a string or a list of parts
    if isinstance(result.content, str):
        content = result.content.strip().lower()
    else:
        # If it's a list, join the text parts together
        content = "".join([
            part.get("text", "") if isinstance(part, dict) else str(part) 
            for part in result.content
        ]).strip().lower()

    if "catalog" in content:
        next_agent = "catalog_agent"
    elif "recommend" in content:
        next_agent = "recommendation_agent"
    elif "order" in content:
        next_agent = "order_agent"
    elif "support" in content:
        next_agent = "support_agent"
    else:
        next_agent = END

    return {"next_agent": next_agent}


def route_from_supervisor(state: State):
    """Conditional edge: reads next_agent set by the supervisor node."""
    return state.get("next_agent", END)
