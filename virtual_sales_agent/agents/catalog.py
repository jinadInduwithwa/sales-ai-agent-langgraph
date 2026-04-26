"""
Agent 2 — Catalog Agent
Handles product browsing: listing categories and searching products.
Tools: get_available_categories, search_products
"""

from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END
from langgraph.prebuilt import tools_condition

from virtual_sales_agent.llm import llm
from virtual_sales_agent.state import State
from virtual_sales_agent.tools import get_available_categories, search_products
from virtual_sales_agent.utils import Agent

catalog_tools = [get_available_categories, search_products]

_catalog_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a product catalog specialist for an online store.

Your responsibilities:
- List all available product categories using the get_available_categories tool
- Search for products by name, category, or price range using the search_products tool
- Present results clearly in bullet points: name, price, stock availability

If a search returns no results, retry with broader criteria (remove filters or use different keywords).
Always be helpful and suggest alternatives when exact matches are not found.

Current user: {user_info} | Current time: {time}""",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

_catalog_runnable = _catalog_prompt | llm.bind_tools(catalog_tools)
catalog_agent = Agent(_catalog_runnable)


def route_catalog(state: State):
    """Route catalog agent to its tools or END."""
    result = tools_condition(state)
    return "catalog_tools" if result == "tools" else END
