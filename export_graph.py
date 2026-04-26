# Create a file named 'export_graph.py'
from virtual_sales_agent.graph import graph
with open("graph_viz.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())
print("Graph saved to graph_viz.png")

