"""
The logic builder (Member 3): which symbol may come next in an expression.

There is no Tkinter in this file, so it can be tested on its own.
"""

BINARY = ("AND", "OR", "->")        # operators that need a left AND a right side

# For each kind of symbol, which kinds may come right after it?
ALLOWED_AFTER = {
    "START": ["VAR", "NOT", "("],
    "VAR":   ["BINOP", ")"],
    "BINOP": ["VAR", "NOT", "("],
    "NOT":   ["VAR", "NOT", "("],
    "(":     ["VAR", "NOT", "("],
    ")":     ["BINOP", ")"],
}


def tokenize(text):
    """Cut the text into symbols: '(A AND B)' -> ['(', 'A', 'AND', 'B', ')']."""
    spaced = text.replace("(", " ( ").replace(")", " ) ").replace("->", " -> ")
    return spaced.split()


def kind_of(token):
    """Say what KIND of symbol this is: BINOP, NOT, '(', ')' or VAR."""
    if token.upper() in BINARY:
        return "BINOP"
    if token.upper() == "NOT":
        return "NOT"
    if token in ("(", ")"):
        return token
    return "VAR"            # anything else is treated as a variable


def open_brackets(tokens):
    """How many brackets are open right now."""
    count = 0
    for token in tokens:
        if token == "(":
            count += 1
        elif token == ")":
            count -= 1
    return count


def can_add(tokens, token):
    """May `token` come next, after the symbols in `tokens`?"""
    if tokens:
        previous = kind_of(tokens[-1])
    else:
        previous = "START"

    kind = kind_of(token)
    if kind not in ALLOWED_AFTER[previous]:
        return False
    if kind == ")" and open_brackets(tokens) <= 0:
        return False        # nothing is open, so there is nothing to close
    return True