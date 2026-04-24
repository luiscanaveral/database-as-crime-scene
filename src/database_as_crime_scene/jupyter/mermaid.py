import base64
import uuid

from IPython.display import Image, display
from sqlalchemy import create_engine, inspect


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
