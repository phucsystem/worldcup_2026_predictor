from langgraph.graph import END, START, StateGraph

from app.pipeline.nodes_analyst import analyst_node
from app.pipeline.nodes_collector import collector_node
from app.pipeline.nodes_editor import editor_node
from app.pipeline.state import BriefState


def build_graph():
    g = StateGraph(BriefState)
    g.add_node("collector", collector_node)
    g.add_node("analyst", analyst_node)
    g.add_node("editor", editor_node)
    g.add_edge(START, "collector")
    g.add_edge("collector", "analyst")
    g.add_edge("analyst", "editor")
    g.add_edge("editor", END)
    return g.compile()
