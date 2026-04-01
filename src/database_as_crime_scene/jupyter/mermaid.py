import base64
from IPython.display import Image, display
#import matplotlib.pyplot as plt
import json
import uuid

def draw(graph):
    graphbytes = graph.encode("utf8")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    display(Image(url="https://mermaid.ink/img/" + base64_string))

def format_node_label(node):
    """Create readable label for a plan node."""
    label_parts = [node.get("Node Type", "Unknown")]

    # Add relation if exists
    if "Relation Name" in node:
        label_parts.append(f"Table: {node['Relation Name']}")

    # Add index name
    if "Index Name" in node:
        label_parts.append(f"Index: {node['Index Name']}")

    # Add condition
    if "Index Cond" in node:
        label_parts.append(f"Cond: {node['Index Cond']}")

    # Add timing
    if "Actual Total Time" in node:
        label_parts.append(f"Time: {node['Actual Total Time']} ms")

    # Add rows
    if "Actual Rows" in node:
        label_parts.append(f"Rows: {node['Actual Rows']}")

    return "<br/>".join(label_parts)


def generate_mermaid_from_execution_plan(plan_json):
    """
    Convert PostgreSQL JSON plan into Mermaid flowchart.
    """

    nodes = []
    edges = []

    def walk(node, parent_id=None):
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        label = format_node_label(node)

        nodes.append(f'{node_id}["{label}"]')

        if parent_id:
            edges.append(f"{node_id} --> {parent_id}")

        for child in node.get("Plans", []):
            walk(child, node_id)

        return node_id

    root_plan = plan_json[0]["Plan"]
    walk(root_plan)

    mermaid = "flowchart TD\n"
    for n in nodes:
        mermaid += f"    {n}\n"
    for e in edges:
        mermaid += f"    {e}\n"

    return mermaid