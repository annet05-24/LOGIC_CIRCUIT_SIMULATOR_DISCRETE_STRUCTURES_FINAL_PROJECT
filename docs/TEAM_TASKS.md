# Team Tasks

Three members, one pipeline. Tick boxes as work is finished.

## Member 1: Parsing & Logic Engine (`logic_sim/parsing/`)

- [ ] Tokenizer: variables, `AND`, `OR`, `NOT`, parentheses
- [ ] Parser: tokens → AST (correct precedence: NOT, then AND, then OR)
- [ ] Validation with clear `ExpressionError` messages and positions
- [ ] Rewrite →, ↔, XOR into AND/OR/NOT (if supported)
- [ ] Simplification with Boolean laws (De Morgan, double negation, absorption...)
- [ ] `truth_table(ast)` in the format of CONTRACTS.md

## Member 2: Circuit Generation & Graph Mapping (`logic_sim/circuit/`)

- [ ] AST → gate graph (AND/OR/NOT), one input node per variable
- [ ] Layout: place gates in columns by depth, route wires without messy overlaps
- [ ] `build_circuit(ast)` in the format of CONTRACTS.md
- [ ] `propagate(circuit, assignment)` giving a value for every node

## Member 3: User Interface & Interactive Testing (`logic_sim/ui/`)

- [x] Window: expression box, build button, error label
- [x] One toggle per input variable
- [x] Draw the circuit from the graph
- [x] Highlight wires by 0/1 value
- [ ] Proper gate symbols (AND, OR, NOT shapes)
- [ ] Truth table panel with the current row highlighted
- [ ] Testing dashboard: expected (truth table) vs actual (circuit), mismatch warning
- [ ] Friendly error display

## Shared / integration

- [ ] Agree on and sign off CONTRACTS.md (all three)
- [ ] Set `USE_MOCK = False` in `backend.py` and delete `mock_backend.py`
- [ ] Add many expressions to `tests/test_integration.py`
- [ ] Final end-to-end test and demo

## Suggested order of work

1. **Together:** confirm CONTRACTS.md.
2. **In parallel:** each member builds their module against the contract.
3. **Then:** connect real modules one at a time (parser → circuit, then circuit → UI).
4. **Finally:** integration testing, polish, demo.
