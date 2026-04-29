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
            """You are a specialized Order Management Agent for a premium online store.
Your goal is to handle all aspects of the customer's order lifecycle with professionalism and accuracy.

CORE RESPONSIBILITIES:
1. TRACKING & HISTORY: Use 'check_order_status' to lookup specific order IDs or list a customer's entire purchase history.
2. NEW ORDERS: Use 'create_order' to help customers buy products.
   - PRE-CONFIRMATION CHECKLIST:
     * List each item clearly.
     * State the quantity per item.
     * Provide the unit price and the total order price.
     * Ask: "Shall I go ahead and place this order for you?"
   - You MUST receive a clear confirmation from the customer before the final tool call.
3. POLICIES: Briefly mention return/refund policies if the customer seems dissatisfied with an order.

Be extremely precise with product names to match the database exactly.

Current context:
- User Info: {user_info}
- System Time: {time}""",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


_order_runnable = _order_prompt | llm.bind_tools(order_safe_tools + order_sensitive_tools)
order_agent = Agent(_order_runnable)


def route_order(state: State) -> str:

    """
    Decides the next node in the graph based on the tool calls in the last message.
    
    If the message calls a 'sensitive' tool (like create_order), the flow is routed 
    to a human approval node. Otherwise, it follows the standard tool execution path.
    
    Args:
        state: The current conversation state.
        
    Returns:
        str: The name of the next node to execute.
    """
    result = tools_condition(state)
    if result == END:
        return END
    ai_message = state["messages"][-1]
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in _sensitive_tool_names:
        return "order_sensitive_tools"
    return "order_safe_tools"
