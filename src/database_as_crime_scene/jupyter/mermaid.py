import base64
import json
import os
import re
import uuid

from IPython.display import Image, Javascript, display
from sqlalchemy import create_engine, inspect

execution_nodes_types  = {
    #Scan
    "Seq Scan": "Scans the entire table row by row. This is highly efficient for small tables but a performance bottleneck for large ones.",
    "Index Scan":"Uses a B-tree or other index to find matching pointer locations, then look up those exact rows in the main table.",
    "Index Only Scan":"Satisfies the query completely using just the index file, never touching the actual table. This is the fastest data retrieval method.",
    "Bitmap Index Scan":"A two-part scan. It first maps all matching rows from the index into a memory bitmap, then reads the table blocks in physical order to reduce random disk I/O.",
    # Join
    "Nested Loop":"Iterates through every row of the outer table and looks for matches in the inner table. Ideal for small datasets, especially when the inner table uses an index.",
    "Hash Join":"Builds a temporary hash table in memory from the smaller dataset, then scans the larger dataset to find instant matches. Highly efficient for large, unsorted datasets.",
    "Merge Join":" Takes two sorted datasets and zips them together side by side. It is incredibly fast if the data is already sorted by an index or explicit sort node.",
    #Aux
    "Sort":"Orders the rows based on your ORDER BY clause or to prepare for a Merge Join.",
    "Hash":"A child step that transforms a dataset into an in-memory hash map to assist a Hash Join node",
    "Aggregate":"Implements group operations like SUM(), COUNT(), or AVG() using either sorting or hashing.",
    "Gather":"Indicates a parallel query where worker processes are coordinated to read data concurrently, and a Gather node merges their results back",
    "":"",
}

execution_nodes_colors = {
    "Seq Scan": "#3498db",
    "Index Scan": "#2980b9",
    "Index Only Scan": "#1abc9c",
    "Bitmap Index Scan": "#9b59b6",
    "Nested Loop": "#e67e22",
    "Hash Join": "#d35400",
    "Merge Join": "#e74c3c",
    "Sort": "#2ecc71",
    "Hash": "#1abc9c",
    "Aggregate": "#f39c12",
    "Gather": "#95a5a6",
}


def draw(graph):
    graphbytes = graph.encode("utf8")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    url = "https://mermaid.ink/img/" + base64_string
    display(Image(url=url))
    display(url)


def _plan_node_to_text(node, depth=0):
    indent = "  " * depth
    node_type = node.get("Node Type", "Unknown")
    relation = node.get("Relation Name", "")
    startup_cost = node.get("Startup Cost", 0)
    total_cost = node.get("Total Cost", 0)
    rows = node.get("Plan Rows", 0)
    width = node.get("Plan Width", 0)

    prefix = "-> " if depth > 0 else ""
    relation_part = f" on {relation}" if relation else ""
    line = f"{indent}{prefix}{node_type}{relation_part}  (cost={startup_cost}..{total_cost} rows={rows} width={width})"

    props = []
    for key in ["Strategy", "Filter", "Index Cond", "Hash Cond", "Join Filter",
                 "Sort Key", "Sort Method", "Group Key", "Merge Cond"]:
        if key in node:
            val = node[key]
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            props.append(f"{indent}  {key}: {val}")

    plan_lines = [line] + props
    for child in node.get("Plans", []):
        plan_lines.append(_plan_node_to_text(child, depth + 1))

    return "\n".join(plan_lines)


def _json_plan_to_text(plan_json):
    plan_obj = plan_json[0] if isinstance(plan_json, list) else plan_json
    plan = plan_obj["Plan"]
    lines = [_plan_node_to_text(plan)]

    planning_time = plan_obj.get("Planning Time")
    execution_time = plan_obj.get("Execution Time")
    if planning_time is not None:
        lines.append(f"Planning Time: {planning_time} ms")
    if execution_time is not None:
        lines.append(f"Execution Time: {execution_time} ms")

    return "\n".join(lines)


def draw_execution_plan(plan_json):
    text_plan = _json_plan_to_text(plan_json)
    plugin_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..",
        ".local", "notebook", "jslib", "pg-plan-diagram.min.js"
    )
    if os.path.exists(plugin_path):
        with open(plugin_path) as f:
            plugin_js = f.read()
    else:
        plugin_js = ""

    plugin_js_global = re.sub(
        r'export\{\w+ as default,(\w+) as pgPlanDiagram\};',
        r'window.pgPlanDiagram = window.pgPlanDiagram || \1;',
        plugin_js
    )

    plan_json_str = json.dumps(text_plan)

    js = f"""(function() {{
    var text = {plan_json_str};
    var container = element;
    if (!container || container.nodeType !== 1) {{
        container = document.querySelector('.jp-OutputArea-output') ||
                    document.querySelector('.output_area') ||
                    document.body;
    }}
    var mermaidDiv = document.createElement('div');
    mermaidDiv.className = 'mermaid';
    mermaidDiv.textContent = 'pg-plan\\n' + text;
    container.appendChild(mermaidDiv);

    function runMermaid() {{
        try {{
            mermaid.run({{ nodes: [mermaidDiv] }});
        }} catch(e) {{
            console.warn('mermaid.run failed', e);
        }}
    }}

    if (typeof mermaid !== 'undefined' && mermaid.run) {{
        runMermaid();
    }} else if (!window.__pgPlanLoading__) {{
        window.__pgPlanLoading__ = true;
        var s1 = document.createElement('script');
        s1.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
        s1.onload = function() {{
            {plugin_js_global}
            try {{ mermaid.registerExternalDiagrams([window.pgPlanDiagram]); }} catch(e) {{ console.warn('pg-plan plugin registration failed', e); }}
            mermaid.initialize({{ startOnLoad: false }});
            runMermaid();
        }};
        document.head.appendChild(s1);
    }}
}})();"""
    display(Javascript(js))


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

    return " | ".join(label_parts)


def generate_mermaid_from_execution_plan(plan_json, diagram_type="flowchart"):
    """
    Convert PostgreSQL JSON plan into a Mermaid diagram.
    Supported diagram_type values: "flowchart" (default), "state".
    """

    node_defs = []
    edges = []
    note_data = []
    node_classes = []
    class_defs = {}

    def walk(node, parent_id=None):
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        label = format_node_label(node)

        node_defs.append((node_id, label))

        node_type = node.get("Node Type", "")
        color = execution_nodes_colors.get(node_type)
        if color:
            class_name = f"type_{node_type.replace(' ', '_')}"
            class_defs[class_name] = color
            node_classes.append((node_id, class_name))

        if parent_id:
            edges.append((node_id, parent_id))

        note_parts = []
        if "Output" in node:
            output_content = node["Output"]
            if isinstance(output_content, list):
                note_parts.append("Output: " + ", ".join(str(o) for o in output_content))
            else:
                note_parts.append(f"Output: {output_content}")
        if "Group Key" in node:
            group_key = node["Group Key"]
            if isinstance(group_key, list):
                note_parts.append("Group Key: " + ", ".join(str(o) for o in group_key))
            else:
                note_parts.append(f"Group Key: {group_key}")
        if note_parts:
            note_data.append((node_id, note_parts))

        for child in node.get("Plans", []):
            walk(child, node_id)

        return node_id

    root_plan = plan_json[0]["Plan"]
    walk(root_plan)

    if diagram_type == "state":
        mermaid = "stateDiagram-v2\n"
        for node_id, label in node_defs:
            label_repr = label.replace('"', '\\"')
            mermaid += f'    state "{label_repr}" as {node_id}\n'
        for node_id, parts in note_data:
            mermaid += f"    note right of {node_id}\n    " + "\n    ".join(parts) + "\nend note\n"
    else:
        mermaid = "flowchart TD\n"
        for node_id, label in node_defs:
            mermaid += f'    {node_id}["{label}"]\n'
        for node_id, parts in note_data:
            out_id = f"out_{node_id}"
            mermaid += f'    {out_id}["{" | ".join(parts)}"]:::outputnote\n'
            mermaid += f"    {node_id} --> {out_id}\n"
        if note_data:
            mermaid += "    classDef outputnote fill:#ffcc00;\n"

    for child_id, parent_id in edges:
        mermaid += f"    {child_id} --> {parent_id}\n"
    for class_name, color in class_defs.items():
        mermaid += f"    classDef {class_name} fill:{color};\n"
    for node_id, class_name in node_classes:
        mermaid += f"    class {node_id} {class_name};\n"

    return mermaid


def get_mermaid_by_table_name(
    connection_string: str, schemaname: str, tablename: str
) -> str:
    """
    Connect to a database using SQLAlchemy and return a Mermaid ER diagram
    for the specified table and its immediate relationships.
    """
    engine = create_engine(connection_string)
    inspector = inspect(engine)

    tables_to_include = {tablename}

    try:
        all_tables = inspector.get_table_names(schema=schemaname)
    except Exception as e:
        print(f"Error reading schema {schemaname}: {e}")
        return "erDiagram\n"

    relationships = []

    for t in all_tables:
        try:
            fks = inspector.get_foreign_keys(t, schema=schemaname)
            for fk in fks:
                if t == tablename or fk["referred_table"] == tablename:
                    tables_to_include.add(t)
                    tables_to_include.add(fk["referred_table"])
                    relationships.append(
                        {
                            "from": t,
                            "to": fk["referred_table"],
                            "name": fk.get("name") or f"fk_{t}_{fk['referred_table']}",
                        }
                    )
        except Exception:
            # Skip tables that we can't inspect
            pass

    mermaid = ["erDiagram"]

    for t in sorted(list(tables_to_include)):
        mermaid.append(f"    {t} {{")
        try:
            columns = inspector.get_columns(t, schema=schemaname)
            pk_constraint = inspector.get_pk_constraint(t, schema=schemaname)
            pks = pk_constraint.get("constrained_columns", []) if pk_constraint else []

            fk_columns = set()
            for fk in inspector.get_foreign_keys(t, schema=schemaname):
                for c in fk["constrained_columns"]:
                    fk_columns.add(c)

            for c in columns:
                col_type = str(c["type"]).split("(")[0]
                # Filter out spaces and some problematic chars in mermaid types
                col_type = col_type.replace(" ", "_")
                col_name = c["name"]

                modifiers = []
                if col_name in pks:
                    modifiers.append("PK")
                if col_name in fk_columns:
                    modifiers.append("FK")

                modifier_str = " ".join(modifiers)
                if modifier_str:
                    mermaid.append(f"        {col_type} {col_name} {modifier_str}")
                else:
                    mermaid.append(f"        {col_type} {col_name}")
        except Exception as e:
            # If we fail to read columns, just create an empty table representation
            print(f"Failed to read columns for table {t}: {e}")
            pass

        mermaid.append("    }")

    # Use many-to-one default syntax since foreign key represents many-to-one relationship
    for rel in relationships:
        mermaid.append(f'    {rel["from"]} }}o--|| {rel["to"]} : "{rel["name"]}"')

    return "\n".join(mermaid)


def get_mermaid_by_view_name(
    connection_string: str, schemaname: str, viewname: str
) -> str:
    """
    Connect to a database using SQLAlchemy and return a Mermaid ER diagram
    for the specified view. Views usually do not have explicit foreign keys,
    so this primarily lists the view's columns.
    """
    engine = create_engine(connection_string)
    inspector = inspect(engine)

    try:
        all_views = inspector.get_view_names(schema=schemaname)
        if viewname not in all_views:
            print(f"View {viewname} not found in schema {schemaname}")
            return "erDiagram\n"
    except Exception as e:
        print(f"Error reading views for schema {schemaname}: {e}")
        return "erDiagram\n"

    mermaid = ["erDiagram"]
    mermaid.append(f"    {viewname} {{")

    try:
        columns = inspector.get_columns(viewname, schema=schemaname)
        for c in columns:
            col_type = str(c["type"]).split("(")[0].replace(" ", "_")
            col_name = c["name"]
            mermaid.append(f"        {col_type} {col_name}")
    except Exception as e:
        print(f"Failed to read columns for view {viewname}: {e}")

    mermaid.append("    }")
    return "\n".join(mermaid)
