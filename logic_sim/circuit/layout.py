"""Place circuit nodes within the UI's fixed 600 by 300 canvas.

Columns: inputs on the left, then one column per gate depth, then OUT.
Rows: each gate tries to sit at the average height of the nodes that feed it
(the "barycenter" heuristic), which keeps wires short and reduces crossings.
Gates in the same column are then pushed apart so they do not overlap.
"""

WIDTH, HEIGHT = 600, 300
INPUT_X, OUTPUT_X = 40, 560    # centers of the input column and of OUT
TOP, BOTTOM = 30, 270          # gate centers stay in this range (gates are 44 high)
GATE_GAP = 56                  # vertical distance between gate centers (44 + room)


def place_nodes(circuit, depths):
    columns = {}
    for gate in circuit["gates"]:
        columns.setdefault(depths[gate["id"]], []).append(gate)
    max_depth = max(columns, default=0)
    step = (OUTPUT_X - INPUT_X) / (max_depth + 1)   # equal spacing, OUT included
    position = {}

    # Inputs: evenly spaced, kept in order of first use (the truth table's order).
    inputs = circuit["inputs"]
    for index, node in enumerate(inputs):
        node["x"] = INPUT_X
        node["y"] = round(HEIGHT * (index + 1) / (len(inputs) + 1))
        position[node["id"]] = node["y"]

    # Gates: one column at a time, left to right, so sources are already placed.
    for depth in sorted(columns):
        gates = columns[depth]
        wanted = {g["id"]: sum(position[s] for s in g["inputs"]) / len(g["inputs"])
                  for g in gates}
        gates.sort(key=lambda g: wanted[g["id"]])    # stable: ties keep their order
        ys = _spread([wanted[g["id"]] for g in gates], GATE_GAP, TOP, BOTTOM)
        for gate, y in zip(gates, ys):
            gate["x"] = round(INPUT_X + depth * step)
            gate["y"] = round(y)
            position[gate["id"]] = gate["y"]

    # OUT sits level with the node it comes from, so the last wire is straight.
    circuit["output"].update(x=OUTPUT_X, y=position[circuit["output"]["from"]])


def _spread(wanted, gap, low, high):
    """Move sorted heights as little as possible so neighbours are `gap` apart.

    If the column is too crowded to fit, the gap shrinks so everything stays
    inside [low, high].
    """
    if len(wanted) > 1:
        gap = min(gap, (high - low) / (len(wanted) - 1))
    ys = []
    for y in wanted:                       # push down past the previous gate
        ys.append(max(y, low, ys[-1] + gap if ys else low))
    if ys and ys[-1] > high:               # ran off the bottom: push back up
        ys[-1] = high
        for i in range(len(ys) - 2, -1, -1):
            ys[i] = min(ys[i], ys[i + 1] - gap)
    return ys
