import json
import uuid


# ==========================================================
# CONFIG
# ==========================================================

SLOW_THRESHOLD_MS = 50
MEDIUM_THRESHOLD_MS = 10


# ==========================================================
# NODE LABEL BUILDER
# ==========================================================

def format_label(node):
    lines = []

    node_type = node.get("Node Type", "Unknown")
    lines.append(f"<b>{node_type}</b>")

    if "Relation Name" in node:
        lines.append(f"Table: {node['Relation Name']}")

    if "Index Name" in node:
        lines.append(f"Index: {node['Index Name']}")

    startup = node.get("Actual Startup Time", 0)
    total = node.get("Actual Total Time", 0)

    lines.append(f"Time: {startup:.2f} → {total:.2f} ms")

    rows = node.get("Actual Rows")
    loops = node.get("Actual Loops")

    if rows is not None:
        lines.append(f"Rows: {rows}")

    if loops is not None:
        lines.append(f"Loops: {loops}")

    for cond in [
        "Hash Cond",
        "Merge Cond",
        "Index Cond",
        "Filter",
        "Join Filter",
    ]:
        if cond in node:
            lines.append(f"{cond}: {node[cond]}")

    if "Sort Method" in node:
        lines.append(
            f"Sort: {node['Sort Method']} "
            f"({node.get('Sort Space Used','')}kB)"
        )

    if "Shared Hit Blocks" in node:
        lines.append(f"Buffer Hits: {node['Shared Hit Blocks']}")

    return "<br/>".join(lines)


# ==========================================================
# PERFORMANCE CLASSIFICATION
# ==========================================================

def classify_node(node):
    time = node.get("Actual Total Time", 0)

    if time >= SLOW_THRESHOLD_MS:
        return "slow"
    elif time >= MEDIUM_THRESHOLD_MS:
        return "medium"
    return "fast"


# ==========================================================
# TREE → MERMAID
# ==========================================================

def build_execution_tree(plan):

    nodes = []
    edges = []

    def walk(node, parent=None):

        node_id = f"N{uuid.uuid4().hex[:6]}"
        label = format_label(node)
        cls = classify_node(node)

        nodes.append(f'{node_id}["{label}"]:::{cls}')

        if parent:
            edges.append(f"{node_id} --> {parent}")

        for child in node.get("Plans", []):
            walk(child, node_id)

    walk(plan)

    mermaid = "flowchart TD\n"

    for n in nodes:
        mermaid += f"    {n}\n"

    for e in edges:
        mermaid += f"    {e}\n"

    mermaid += STYLE_BLOCK

    return mermaid


# ==========================================================
# FLAMEGRAPH GENERATOR 🔥
# ==========================================================

def build_flamegraph(plan):

    lines = ["flowchart LR"]

    def walk(node, parent=None):

        node_id = f"F{uuid.uuid4().hex[:6]}"
        node_type = node.get("Node Type")

        time = node.get("Actual Total Time", 0)
        width = max(1, int(time * 5))

        label = f"{node_type}<br/>{time:.2f} ms"
        cls = classify_node(node)

        lines.append(
            f'{node_id}["{label}"]:::{cls}'
        )

        if parent:
            lines.append(f"{parent} --> {node_id}")

        for child in node.get("Plans", []):
            walk(child, node_id)

    walk(plan)

    lines.append(STYLE_BLOCK)

    return "\n".join(lines)


# ==========================================================
# COLORS
# ==========================================================

STYLE_BLOCK = """
classDef fast fill:#d8f3dc,stroke:#1b4332,stroke-width:1px;
classDef medium fill:#fff3b0,stroke:#e09f3e,stroke-width:2px;
classDef slow fill:#ffccd5,stroke:#d00000,stroke-width:3px;
"""


# ==========================================================
# MAIN
# ==========================================================

def main():

    with open("explain.json") as f:
        data = json.load(f)

    plan = data[0]["Plan"]

    tree = build_execution_tree(plan)
    flame = build_flamegraph(plan)

    with open("execution_plan.mmd", "w") as f:
        f.write(tree)

    with open("flamegraph_plan.mmd", "w") as f:
        f.write(flame)

    print("✅ Mermaid diagrams generated:")
    print("   execution_plan.mmd")
    print("   flamegraph_plan.mmd")


if __name__ == "__main__":
    main()