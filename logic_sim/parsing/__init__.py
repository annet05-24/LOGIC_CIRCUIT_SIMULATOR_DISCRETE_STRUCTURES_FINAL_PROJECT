"""Member 1: expression parsing and truth-table generation.

The public AST format follows docs/CONTRACTS.md so the circuit and UI
members can use it directly:
    VAR: {"type": "VAR", "name": "A"}
    NOT: {"type": "NOT", "operand": node}
    AND/OR: {"type": "AND" or "OR", "left": node, "right": node}

Supported input: uppercase single-letter variables A-Z, parentheses, AND,
OR, NOT and their common symbols. IMPLIES and IFF are also accepted and are
rewritten into AND/OR/NOT before returning the AST.
"""

from itertools import product

# Reuse the tested recursive-descent parser and simplification engine supplied
# in the project root as logic_engine.py.
import logic_engine as _engine


class ExpressionError(ValueError):
    """Raised when an expression is invalid or outside the project grammar."""

    def __init__(self, message, position=None):
        self.position = position
        self.message = message
        suffix = f" at position {position}" if position is not None else ""
        super().__init__(message + suffix)


def _to_contract_ast(node):
    """Convert the engine's class-based AST to the agreed dictionary AST."""
    if isinstance(node, _engine.Var):
        # The circuit project contract uses A-Z single-character variable names.
        if len(node.name) != 1 or node.name not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            raise ExpressionError(
                f"Invalid variable '{node.name}'. Use uppercase letters A-Z only."
            )
        return {"type": "VAR", "name": node.name}
    if isinstance(node, _engine.Not):
        return {"type": "NOT", "operand": _to_contract_ast(node.child)}
    if isinstance(node, _engine.And):
        return {"type": "AND", "left": _to_contract_ast(node.left),
                "right": _to_contract_ast(node.right)}
    if isinstance(node, _engine.Or):
        return {"type": "OR", "left": _to_contract_ast(node.left),
                "right": _to_contract_ast(node.right)}
    raise ExpressionError("Constants are not supported. Use variables A-Z.")


def parse(expression):
    """Convert an expression string into the dictionary AST in CONTRACTS.md."""
    if not isinstance(expression, str):
        raise ExpressionError("Expression must be text.")
    try:
        original = _engine.parse(expression)
        # Eliminate implication and biconditional; circuit gates only support
        # AND, OR and NOT. This also applies basic Boolean simplification.
        simplified, _steps = _engine.simplify(original)
        return _to_contract_ast(simplified)
    except _engine.ParseError as error:
        raise ExpressionError(error.message, error.position) from error
    except RecursionError as error:
        raise ExpressionError("Expression is too deeply nested.") from error


def _walk_variables(ast, found):
    if not isinstance(ast, dict):
        raise ExpressionError("Invalid AST: each node must be a dictionary.")
    node_type = ast.get("type")
    if node_type == "VAR":
        name = ast.get("name")
        if not isinstance(name, str) or len(name) != 1 or name not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            raise ExpressionError("Invalid AST variable name; expected A-Z.")
        if name not in found:
            found.append(name)
    elif node_type == "NOT":
        if "operand" not in ast:
            raise ExpressionError("Invalid NOT node: missing operand.")
        _walk_variables(ast["operand"], found)
    elif node_type in ("AND", "OR"):
        if "left" not in ast or "right" not in ast:
            raise ExpressionError(f"Invalid {node_type} node: missing left or right child.")
        _walk_variables(ast["left"], found)
        _walk_variables(ast["right"], found)
    else:
        raise ExpressionError(f"Invalid AST node type: {node_type!r}.")


def _evaluate(ast, assignment):
    node_type = ast["type"]
    if node_type == "VAR":
        return bool(assignment[ast["name"]])
    if node_type == "NOT":
        return not _evaluate(ast["operand"], assignment)
    if node_type == "AND":
        return _evaluate(ast["left"], assignment) and _evaluate(ast["right"], assignment)
    if node_type == "OR":
        return _evaluate(ast["left"], assignment) or _evaluate(ast["right"], assignment)
    raise ExpressionError(f"Invalid AST node type: {node_type!r}.")


def truth_table(ast):
    """Return variables and rows in the exact format required by CONTRACTS.md.

    Rows start with all inputs set to 0 and count upward in binary.
    """
    names = []
    _walk_variables(ast, names)
    rows = []
    for values in product([0, 1], repeat=len(names)):
        inputs = dict(zip(names, values))
        rows.append({"inputs": inputs, "output": int(_evaluate(ast, inputs))})
    return {"variables": names, "rows": rows}


__all__ = ["ExpressionError", "parse", "truth_table"]
