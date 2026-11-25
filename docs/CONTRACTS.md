# Data Contracts

These are the exact formats passed between modules. **Do not change a format without
telling the other two members**: this file is what lets three people build in parallel.

Everything is plain Python dicts, lists, strings and ints (no custom classes).

---

## 1. Expression (UI → Member 1)

A string such as `"(A AND B) OR NOT C"`.
Variables are single uppercase letters (A–Z). Operators: `AND`, `OR`, `NOT`, parentheses.

## 2. Errors (Member 1 → UI)

Any invalid input raises `ExpressionError` (a subclass of `ValueError`):

```python
raise ExpressionError("Unexpected ')'", position=7)
```

The UI catches `ValueError` and shows `str(error)` in red.

## 3. AST (Member 1 → Member 2)

Nested dicts with only four node types:

```python
{"type": "VAR", "name": "A"}
{"type": "NOT", "operand": <node>}
{"type": "AND", "left": <node>, "right": <node>}
{"type": "OR",  "left": <node>, "right": <node>}
```

Example: `(A AND B) OR NOT C`

```python
{"type": "OR",
 "left":  {"type": "AND",
           "left":  {"type": "VAR", "name": "A"},
           "right": {"type": "VAR", "name": "B"}},
 "right": {"type": "NOT", "operand": {"type": "VAR", "name": "C"}}}
```

## 4. Truth table (Member 1 → UI and tests)

Rows are in binary counting order, first variable most significant, starting at all zeros.

```python
{"variables": ["A", "B", "C"],
 "rows": [
   {"inputs": {"A": 0, "B": 0, "C": 0}, "output": 1},
   {"inputs": {"A": 0, "B": 0, "C": 1}, "output": 0},
   ...
 ]}
```

## 5. Circuit graph (Member 2 → UI)

```python
{
  "inputs": [ {"id": "A", "x": 60, "y": 70}, ... ],
  "gates":  [ {"id": "g1", "type": "AND", "x": 230, "y": 105, "inputs": ["A", "B"]}, ... ],
  "output": {"id": "OUT", "x": 540, "y": 160, "from": "g3"}
}
```

Rules:
- `x`, `y` are the **center** of the node, in a 600×300 coordinate space.
- A gate's `inputs` list holds ids of input nodes or other gates (a wire goes from each).
- **Gates are listed in evaluation order**: a gate's inputs always appear earlier in the list.
- `type` is `"AND"`, `"OR"` (2 inputs) or `"NOT"` (1 input).
- A variable used several times is ONE input node whose id appears in several gates' `inputs`.
- Every id is unique.

Optional `wires` (added by Member 2's layout): one entry per gate input, already
routed around the gates. If it is present the UI draws these lines; if not, the UI
draws simple wires itself.

```python
"wires": [ {"from": "A", "to": "g2", "points": [54, 100, 80, 100, 80, 160, 168, 160]}, ... ]
```

- `points` is a flat list `x1, y1, x2, y2, ...` made only of horizontal and vertical lines.
- A wire is colored by the value of its `from` node.
- The wire from the last gate to `OUT` is not in this list (it is always straight).

## 6. Propagation (UI → Member 2 → UI)

Input: the circuit and an assignment `{"A": 1, "B": 0, "C": 1}`.
Output: a value (0 or 1) for **every** id: inputs, gates and the output node.

```python
{"A": 1, "B": 0, "C": 1, "g1": 0, "g2": 0, "g3": 0, "OUT": 0}
```

The UI colors a wire by the value of the node it comes from.
