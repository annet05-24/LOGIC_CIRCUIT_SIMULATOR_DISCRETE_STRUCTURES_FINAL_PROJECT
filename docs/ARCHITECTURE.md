# System Architecture

## 1. Purpose

Bridge propositional logic and digital circuit design: the user types an expression,
and the system builds, draws and simulates the equivalent AND/OR/NOT circuit.

## 2. The pipeline

```
                 ┌──────────────────────────────────────────────┐
                 │               MEMBER 3: UI                    │
                 │  input box · toggles · canvas · dashboard     │
                 └───────┬──────────────────────────▲───────────┘
        expression text  │                          │  circuit graph, wire values,
        + input values   │                          │  truth table, error messages
                         ▼                          │
                 ┌──────────────────────────────────┴───────────┐
                 │          logic_sim/backend.py (facade)        │
                 └───────┬──────────────────────────▲───────────┘
                         │                          │
            ┌────────────▼───────────┐   AST   ┌─────┴──────────────────┐
            │   MEMBER 1: parsing    ├────────►│   MEMBER 2: circuit    │
            │ tokenize → AST →       │         │ AST → gates/wires →    │
            │ validate → simplify →  │         │ layout → propagation   │
            │ truth table            │         │                        │
            └────────────────────────┘         └────────────────────────┘
```

Data also flows backwards: when the user toggles an input, the UI sends the new
input values to Member 2's propagation engine and redraws with the result.

## 3. Modules

| Module | Package | Public functions |
|---|---|---|
| Parsing & Logic Engine | `logic_sim.parsing` | `parse(expression)`, `truth_table(ast)`, `ExpressionError` |
| Circuit Generation | `logic_sim.circuit` | `build_circuit(ast)`, `propagate(circuit, assignment)` |
| User Interface | `logic_sim.ui` | `run()` |
| Facade | `logic_sim.backend` | `get_circuit(expression)`, `get_truth_table(expression)`, `propagate(circuit, assignment)` |

Exact inputs and outputs are in [CONTRACTS.md](CONTRACTS.md).

## 3.1 Dependency rules

- The **UI imports only `backend`**. It never imports `parsing` or `circuit` directly.
- `parsing` and `circuit` **never import the UI**.
- `circuit` does not import `parsing`; it receives the AST as plain data (dicts).

These rules mean each person can work and test their own part independently.

## 4. Typical interaction

1. User types `(A AND B) -> NOT C` and clicks **Build circuit**.
2. UI calls `backend.get_circuit(text)`.
   - Facade calls `parsing.parse(text)`, which returns an AST (or raises `ExpressionError`).
   - Facade passes the AST to `circuit.build_circuit(ast)`, which returns the circuit graph.
3. UI creates one toggle per input variable and draws the circuit.
4. User flips a toggle. UI calls `backend.propagate(circuit, {"A":1,"B":0,"C":1})`.
5. UI recolors every wire and gate using the returned values.
6. UI shows the truth table (from `backend.get_truth_table`) and highlights the row
   matching the current toggles.

## 5. Two independent ways to compute the same answer

| Route | Owner | How |
|---|---|---|
| Truth table | Member 1 | evaluates the AST directly |
| Circuit simulation | Member 2 | pushes signals through the gate graph |

The final validation (`tests/test_integration.py`) checks that both agree on every row.
A disagreement means a bug in AST evaluation, gate mapping, or propagation.

## 6. Design decisions (proposed defaults: change only if all three agree)

| Question | Proposed decision |
|---|---|
| Operators beyond AND/OR/NOT (→, ↔, XOR)? | Accepted by the parser, then rewritten into AND/OR/NOT by Member 1 before the AST is passed on. Member 2 only ever sees VAR, NOT, AND, OR. |
| Draw the original or the simplified expression? | Show the circuit for the expression as typed; offer simplification as an option. |
| Repeated variables (e.g. A used twice)? | One input node, with several wires fanning out (Member 2). |
| Gate inputs | AND/OR take exactly 2 inputs; NOT takes 1. `A AND B AND C` becomes two chained gates. |
| Variable limit | Maximum 8 variables (2⁸ = 256 truth-table rows). More is rejected with an error. |
| Coordinates | Member 2 gives x/y in a fixed 600×300 space; the UI draws them as given. |
| Errors | Always `ExpressionError` (a `ValueError`) with a human-readable message. |

## 7. Technology

- Python 3.9+
- Tkinter (standard library) for the interface, drawing on a Canvas
- `unittest` for tests
- No third-party dependencies

## 8. Possible future work

- XOR/NAND/NOR gates
- Export the circuit as an image
- Step-by-step signal animation
