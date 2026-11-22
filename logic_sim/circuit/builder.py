"""Build an ordered gate graph from the shared AST format."""
from .layout import place_nodes


def build_circuit(ast):
    """Return a circuit graph for an AST of VAR, NOT, AND and OR nodes."""
    inputs, gates, depths = {}, [], {}

    def visit(node):
        if not isinstance(node, dict):
            raise ValueError("AST nodes must be dictionaries")
        kind = node.get("type")
        if kind == "VAR":
            name = node.get("name")
            if not isinstance(name, str) or len(name) != 1 or name not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                raise ValueError("Variable names must be single uppercase letters")
            if name not in inputs:
                inputs[name] = {"id": name}
                depths[name] = 0
            return name
        if kind not in ("NOT", "AND", "OR"):
            raise ValueError("Unknown AST node type: " + str(kind))
        fields = ("operand",) if kind == "NOT" else ("left", "right")
        if any(field not in node for field in fields):
            raise ValueError("Missing operand for " + kind)
        sources = [visit(node[field]) for field in fields]
        gate_id = "g" + str(len(gates) + 1)
        gates.append({"id": gate_id, "type": kind, "inputs": sources})
        depths[gate_id] = 1 + max(depths[source] for source in sources)
        return gate_id

    source = visit(ast)
    circuit = {"inputs": list(inputs.values()), "gates": gates,
               "output": {"id": "OUT", "from": source}}
    place_nodes(circuit, depths)
    return circuit
