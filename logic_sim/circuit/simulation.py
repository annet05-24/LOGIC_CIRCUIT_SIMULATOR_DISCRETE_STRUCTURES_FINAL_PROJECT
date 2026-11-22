"""Evaluate the circuit graph in its specified gate order."""


def propagate(circuit, assignment):
    """Return the 0/1 signal for each input, gate and output node."""
    values = {}
    for node in circuit["inputs"]:
        name = node["id"]
        if name not in assignment or assignment[name] not in (0, 1):
            raise ValueError("Expected a 0 or 1 for input " + name)
        values[name] = int(assignment[name])
    for gate in circuit["gates"]:
        signals = [values[source] for source in gate["inputs"]]
        kind = gate["type"]
        if kind == "AND" and len(signals) == 2:
            value = signals[0] & signals[1]
        elif kind == "OR" and len(signals) == 2:
            value = signals[0] | signals[1]
        elif kind == "NOT" and len(signals) == 1:
            value = 1 - signals[0]
        else:
            raise ValueError("Invalid gate type or input count: " + str(kind))
        values[gate["id"]] = value
    output = circuit["output"]
    values[output["id"]] = values[output["from"]]
    return values
