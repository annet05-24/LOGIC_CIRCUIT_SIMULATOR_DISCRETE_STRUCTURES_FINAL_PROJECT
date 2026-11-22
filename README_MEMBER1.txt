MEMBER 1 - PARSING AND LOGIC ENGINE

Files supplied:
1. logic_engine.py
   - Tokenizer and recursive-descent parser.
   - Supports AND, OR, NOT, parentheses, symbols, IMPLIES and IFF.
   - Includes AST classes, evaluation, simplification, NNF, equivalence,
     readable expression printing, and a truth-table helper.

2. logic_sim/parsing/__init__.py
   - The adapter used by the team's application.
   - Exposes ExpressionError, parse(expression), and truth_table(ast).
   - Returns the exact dictionary AST and truth-table format agreed in
     docs/CONTRACTS.md.
   - Rewrites IMPLIES and IFF into AND/OR/NOT before passing the AST to
     the circuit-generation member.
   - Enforces the project's A-Z uppercase single-letter variable rule.

3. tests/test_parsing.py
   - Ten tests for precedence, parentheses, symbols, implication/iff
     conversion, truth-table format/order, repeated variables, and errors.

INSTALLATION INTO THE TEAM REPOSITORY

Copy logic_engine.py into the repository root (same level as main.py).
Copy the logic_sim/parsing/__init__.py file over the existing file at
logic_sim/parsing/__init__.py.
Copy tests/test_parsing.py into the repository's tests folder.

Run from the repository root:
    python -m unittest discover -s tests -v

IMPORTANT TEAM INTEGRATION NOTE
The parser returns the dictionary AST agreed in docs/CONTRACTS.md:
  VAR: {"type": "VAR", "name": "A"}
  NOT: {"type": "NOT", "operand": node}
  AND/OR: {"type": "AND" or "OR", "left": node, "right": node}
The truth table is:
  {"variables": ["A", "B"],
   "rows": [{"inputs": {"A": 0, "B": 0}, "output": 0}, ...]}
Rows start at all zeros and count upward in binary.

The app backend currently uses the mock backend. Once Member 2 has finished
and tested build_circuit() and propagate(), the team should set USE_MOCK=False
in logic_sim/backend.py so the real parser and circuit code are used.
