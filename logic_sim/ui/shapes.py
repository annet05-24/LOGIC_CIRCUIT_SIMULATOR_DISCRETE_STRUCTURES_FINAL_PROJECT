"""
Gate shapes for the circuit drawing (Member 3).

Each function takes a gate's CENTER (x, y) and returns a flat list of points
[x1, y1, x2, y2, ...] that canvas.create_polygon() can draw.
"""
import math

GATE_W, GATE_H = 70, 44     # every gate fits in a box this size


def curve(p0, p1, p2, steps=10):
    """A smooth curve from p0 to p2, bent toward p1, made of tiny straight pieces."""
    points = []
    for i in range(steps + 1):
        t = i / steps                       # t goes from 0 to 1
        px = (1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t ** 2 * p2[0]
        py = (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t ** 2 * p2[1]
        points.append(px)
        points.append(py)
    return points


def and_points(x, y):
    """AND: flat left side, flat top and bottom, rounded right side."""
    left = x - GATE_W / 2
    top = y - GATE_H / 2
    bottom = y + GATE_H / 2
    radius = GATE_H / 2
    mid = x + GATE_W / 2 - radius           # where the flat part ends

    points = [left, top]
    for step in range(13):                  # the rounded right side, 12 pieces
        angle = -math.pi / 2 + math.pi * step / 12
        points.append(mid + radius * math.cos(angle))
        points.append(y + radius * math.sin(angle))
    points += [left, bottom]
    return points


def or_points(x, y):
    """OR: a pointed right side and a curved-in left side."""
    left = x - GATE_W / 2
    right = x + GATE_W / 2
    top = y - GATE_H / 2
    bottom = y + GATE_H / 2

    points = []
    points += curve((left, top), (x + 4, top), (right, y))         # top edge to the tip
    points += curve((right, y), (x + 4, bottom), (left, bottom))   # tip to bottom edge
    points += curve((left, bottom), (left + 14, y), (left, top))   # curved-in back
    return points


def not_points(x, y):
    """NOT: a triangle. The small circle on its tip is drawn separately."""
    left = x - GATE_W / 2
    right = x + GATE_W / 2
    top = y - GATE_H / 2
    bottom = y + GATE_H / 2
    tip = right - 10                        # leave room for the small circle
    return [left, top, tip, y, left, bottom]


def points_for(gate_type, x, y):
    """Pick the right shape for a gate type ('AND', 'OR' or 'NOT')."""
    if gate_type == "AND":
        return and_points(x, y)
    if gate_type == "OR":
        return or_points(x, y)
    if gate_type == "NOT":
        return not_points(x, y)
    raise ValueError("Unknown gate type: " + str(gate_type))