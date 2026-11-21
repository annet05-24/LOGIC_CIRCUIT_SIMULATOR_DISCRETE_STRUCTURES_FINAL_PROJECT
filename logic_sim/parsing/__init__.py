"""
MEMBER 1: Parsing and logic engine.

Replace the stubs below with the real implementation (you can split the code
into several files in this folder, e.g. lexer.py, parser.py, simplify.py).
Keep the function names, inputs and outputs exactly as in docs/CONTRACTS.md.
"""


class ExpressionError(ValueError):
    """Raised for any invalid user expression. The UI shows str(error) in red."""

    def __init__(self, message, position=None):
        super().__init__(message)
        self.position = position   # index of the bad character, if known


def parse(expression):
    """expression string -> AST (only VAR, NOT, AND, OR nodes). See CONTRACTS.md."""
    raise NotImplementedError("Member 1: implement parse()")


def truth_table(ast):
    """AST -> truth table dict. See CONTRACTS.md."""
    raise NotImplementedError("Member 1: implement truth_table()")
