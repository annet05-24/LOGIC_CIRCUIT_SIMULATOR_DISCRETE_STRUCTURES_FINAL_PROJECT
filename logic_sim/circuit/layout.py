"""Place circuit nodes within the UI's fixed 600 by 300 canvas."""


def place_nodes(circuit, depths):
    columns = {}
    for node in circuit["inputs"] + circuit["gates"]:
        columns.setdefault(depths[node["id"]], []).append(node)
    max_depth = max(columns)
    for depth, nodes in columns.items():
        x = 60 + 400 * depth / (max_depth + 1)
        for index, node in enumerate(nodes):
            node["x"] = round(x)
            node["y"] = round(300 * (index + 1) / (len(nodes) + 1))
    circuit["output"].update(x=540, y=150)
