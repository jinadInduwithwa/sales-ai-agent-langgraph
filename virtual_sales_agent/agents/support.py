"""
Agent 5 — Customer Support Agent
Handles complaints, store policies, shipping, returns, and general FAQs.
Tools: get_store_policies, check_order_status
"""

from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END
from langgraph.prebuilt import tools_condition

from virtual_sales_agent.llm import llm
from virtual_sales_agent.state import State
from virtual_sales_agent.tools import check_order_status, get_store_policies
from virtual_sales_agent.utils import Agent

support_tools = [get_store_policies, check_order_status]

_support_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a customer support specialist for an online store.

Your responsibilities:
- Answer questions about store policies (returns, shipping, payments, cancellations)
  using the get_store_policies tool
- Look up order details to help resolve order-related complaints or questions
  using the check_order_status tool
- Handle complaints with empathy and provide clear, actionable solutions
- Escalate unresolvable issues politely and explain next steps

Always be professional, patient, and customer-focused.

Current user: {user_info} | Current time: {time}""",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

_support_runnable = _support_prompt | llm.bind_tools(support_tools)
support_agent = Agent(_support_runnable)


def route_support(state: State):
    """Route support agent to its tools or END."""
    result = tools_condition(state)
    return "support_tools" if result == "tools" else END
