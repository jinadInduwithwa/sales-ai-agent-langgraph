"""
Agent 4 — Order Agent
Manages order placement (sensitive — requires human approval) and order status checks.
Tools: check_order_status (safe), create_order (sensitive)
"""

import logging
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END
from langgraph.prebuilt import tools_condition

from virtual_sales_agent.llm import llm
from virtual_sales_agent.state import State
from virtual_sales_agent.tools import check_order_status, create_order
from virtual_sales_agent.utils import Agent

logger = logging.getLogger(__name__)


order_safe_tools = [check_order_status]
order_sensitive_tools = [create_order]
_sensitive_tool_names = {create_order.name}

_order_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an order management specialist for an online store.

Your responsibilities:
- Check individual order status or full order history with the check_order_status tool
- Create new orders with the create_order tool
  → Always confirm product names, quantities, and total cost with the customer BEFORE placing
- Communicate order details, estimated delivery, and tracking information clearly

Be precise about product names and quantities to avoid order errors.

Current user: {user_info} | Current time: {time}""",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

_order_runnable = _order_prompt | llm.bind_tools(order_safe_tools + order_sensitive_tools)
order_agent = Agent(_order_runnable)


def route_order(state: State):
    """Route order agent: safe tools loop back, sensitive tools require human approval."""
    result = tools_condition(state)
    if result == END:
        return END
    ai_message = state["messages"][-1]
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in _sensitive_tool_names:
        return "order_sensitive_tools"
    return "order_safe_tools"
