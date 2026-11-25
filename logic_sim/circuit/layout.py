"""Place circuit nodes and route wires within the UI's fixed 600 by 300 canvas.

This is a small version of the layered ("Sugiyama") graph drawing method:

1. Columns: inputs on the left, one column per gate depth, then OUT.
2. A wire that skips columns gets a reserved lane in every column it passes
   through, so it never runs through a gate.
3. Rows: each gate (and each lane) sits at the average height of what feeds
   it (the "barycenter" heuristic), which keeps wires short and reduces
   crossings. Items in a column are then pushed apart so they do not overlap.
4. Wires: in each gap between two columns, every wire that has to go up or
   down gets its own vertical track, so wires never lie on top of each other.
"""

WIDTH, HEIGHT = 600, 300
INPUT_X, OUTPUT_X = 40, 560    # centers of the input column and of OUT
EDGE = 8                       # keep shapes this far from the top and bottom
GATE_HALF_W, GATE_HALF_H = 35, 22   # gate size used by the UI: 70 x 44
LANE_HALF_H = 4                # a lane only needs room for one wire
MARGIN = 12                    # free space between neighbours in a column
INPUT_R = 14                   # input circle radius used by the UI
PIN_SPACING = 16               # UI: distance between the two inputs of a gate
PIN_INSET = 8                  # UI: wires end this far inside the gate


def place_nodes(circuit, depths):
    gates = circuit["gates"]
    max_depth = max((depths[g["id"]] for g in gates), default=0)
    step = (OUTPUT_X - INPUT_X) / (max_depth + 1)   # equal spacing, OUT included
    column_x = [round(INPUT_X + d * step) for d in range(max_depth + 1)]
    position = {}    # node id -> y

    # Inputs: evenly spaced, kept in order of first use (the truth table's order).
    inputs = circuit["inputs"]
    for index, node in enumerate(inputs):
        node["x"] = INPUT_X
        node["y"] = round(HEIGHT * (index + 1) / (len(inputs) + 1))
        position[node["id"]] = node["y"]

    # One wire per gate input. "lanes" collects its height in each column it skips.
    wires = [{"from": source, "to": gate["id"], "pin": pin, "lanes": []}
             for gate in gates for pin, source in enumerate(gate["inputs"])]
    wires_into = {gate["id"]: [] for gate in gates}
    for wire in wires:
        wires_into[wire["to"]].append(wire)

    def last_y(wire):
        return wire["lanes"][-1] if wire["lanes"] else position[wire["from"]]

    # Columns left to right, so everything that feeds a column is already placed.
    for depth in range(1, max_depth + 1):
        items = []    # (wanted y, half height, gate or wire)
        for gate in gates:
            if depths[gate["id"]] == depth:
                feeds = [last_y(w) for w in wires_into[gate["id"]]]
                items.append((sum(feeds) / len(feeds), GATE_HALF_H, gate))
        for wire in wires:
            if depths[wire["from"]] < depth < depths[wire["to"]]:
                items.append((last_y(wire), LANE_HALF_H, wire))
        items.sort(key=lambda item: item[0])     # stable: ties keep their order
        ys = _spread([i[0] for i in items], [i[1] for i in items])
        for (_, _, thing), y in zip(items, ys):
            if "lanes" in thing:
                thing["lanes"].append(round(y))
            else:
                thing["x"], thing["y"] = column_x[depth], round(y)
                position[thing["id"]] = thing["y"]

    # OUT sits level with the node it comes from, so the last wire is straight.
    circuit["output"].update(x=OUTPUT_X, y=position[circuit["output"]["from"]])
    circuit["wires"] = _route(circuit, wires, depths, column_x)


def _spread(wanted, halves):
    """Move sorted heights as little as possible so neighbours do not overlap.

    `halves` is each item's half height. If the column is too crowded to fit,
    the gaps shrink so everything stays on the canvas.
    """
    if not wanted:
        return []
    gaps = [halves[i] + halves[i + 1] + MARGIN for i in range(len(wanted) - 1)]
    low, high = EDGE + halves[0], HEIGHT - EDGE - halves[-1]
    if sum(gaps) > high - low:
        scale = (high - low) / sum(gaps)
        gaps = [gap * scale for gap in gaps]
    ys = []
    for i, y in enumerate(wanted):              # push down past the previous item
        ys.append(max(y, low if i == 0 else ys[-1] + gaps[i - 1]))
    if ys[-1] > high:                           # ran off the bottom: push back up
        ys[-1] = high
        for i in range(len(ys) - 2, -1, -1):
            ys[i] = min(ys[i], ys[i + 1] - gaps[i])
    return ys


def _route(circuit, wires, depths, column_x):
    """Turn every wire into a list of points made of horizontal and vertical lines."""
    gates = {g["id"]: g for g in circuit["gates"]}
    nodes = dict(gates, **{n["id"]: n for n in circuit["inputs"]})

    # Each wire is a series of hops, one per gap between neighbouring columns.
    # A hop leaves at (x1, y1) and arrives at (x2, y2).
    hops_per_wire = []
    for wire in wires:
        source, target = nodes[wire["from"]], gates[wire["to"]]
        start_depth = depths[source["id"]]
        half = INPUT_R if start_depth == 0 else GATE_HALF_W
        x1, y1 = source["x"] + half, source["y"]
        hops = []
        for offset, lane_y in enumerate(wire["lanes"]):      # pass through lanes
            x = column_x[start_depth + 1 + offset]
            hops.append({"gap": start_depth + offset, "x1": x1, "y1": y1,
                         "x2": x - GATE_HALF_W, "y2": lane_y})
            x1, y1 = x + GATE_HALF_W, lane_y
        count = len(target["inputs"])
        pin_y = target["y"] + (wire["pin"] - (count - 1) / 2) * PIN_SPACING
        hops.append({"gap": depths[target["id"]] - 1, "x1": x1, "y1": y1,
                     "x2": target["x"] - GATE_HALF_W + PIN_INSET, "y2": pin_y})
        hops_per_wire.append(hops)

    # Give each hop that changes height its own vertical track in its gap.
    # Downward hops starting higher, and upward hops starting lower, go further
    # right; this ordering avoids crossings between hops moving the same way.
    gaps = {}
    for hops in hops_per_wire:
        for hop in hops:
            if round(hop["y1"]) != round(hop["y2"]):
                gaps.setdefault(hop["gap"], []).append(hop)
    for gap, hops in gaps.items():
        down = sorted((h for h in hops if h["y2"] > h["y1"]), key=lambda h: -h["y1"])
        up = sorted((h for h in hops if h["y2"] < h["y1"]), key=lambda h: h["y1"])
        left = column_x[gap] + (INPUT_R if gap == 0 else GATE_HALF_W)
        right = column_x[gap + 1] - GATE_HALF_W
        ordered = down + up
        for k, hop in enumerate(ordered):
            hop["turn"] = left + (k + 1) * (right - left) / (len(ordered) + 1)

    routed = []
    for wire, hops in zip(wires, hops_per_wire):
        points = []
        for hop in hops:
            # The first hop starts at the source. Each later hop starts on the
            # right side of a lane, which draws the straight piece through it.
            points += [hop["x1"], hop["y1"]]
            if "turn" in hop:
                points += [hop["turn"], hop["y1"], hop["turn"], hop["y2"]]
            points += [hop["x2"], hop["y2"]]
        routed.append({"from": wire["from"], "to": wire["to"],
                       "points": [round(p) for p in points]})
    return routed
