"""
Agent 3 — Recommendation Agent
Provides personalised product suggestions based on customer preferences.
Tools: search_products_recommendations
"""

from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END
from langgraph.prebuilt import tools_condition
from virtual_sales_agent.llm import llm
from virtual_sales_agent.state import State
from virtual_sales_agent.tools import search_products_recommendations
from virtual_sales_agent.utils import Agent

recommendation_tools = [search_products_recommendations]

_recommendation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a personalised product recommendation specialist for an online store.

Your responsibilities:
- Use the search_products_recommendations tool to find products matching the customer's interests
- Suggest complementary or related items the customer might enjoy
- Explain clearly WHY each product is recommended for this customer
- Focus on in-stock items and respect any stated budget

Always tailor your suggestions to the customer's context and past conversation.

Current user: {user_info} | Current time: {time}""",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

_recommendation_runnable = _recommendation_prompt | llm.bind_tools(recommendation_tools)
recommendation_agent = Agent(_recommendation_runnable)

def route_recommendation(state: State):
    """Route recommendation agent to its tools or END."""
    result = tools_condition(state)
    return "recommendation_tools" if result == "tools" else END
