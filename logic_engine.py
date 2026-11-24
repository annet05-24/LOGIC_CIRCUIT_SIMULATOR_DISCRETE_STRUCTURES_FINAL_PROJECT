"""
logic_engine.py  --  Member 1: Parsing & Logic Engine
Logic Circuit Simulator (CS221 Discrete Structures project)

Pipeline:  text -> tokenize -> parse -> AST -> simplify -> truth_table

Public interface for Members 2 and 3
------------------------------------
    parse(text)                  -> Node            (raises ParseError)
    simplify(node)               -> (Node, steps)   steps = [(law, expr_string), ...]
    to_nnf(node)                 -> (Node, steps)   De Morgan: push negations to variables
    variables(node)              -> list[str]       in order of first appearance
    evaluate(node, assignment)   -> bool
    truth_table(node)            -> list[dict]      each row has the variables and "result"
    equivalent(a, b)             -> bool
    to_string(node)              -> str
    format_truth_table(node)     -> str

AST node classes: Var, Const, Not, And, Or, Implies, Iff
"""

from dataclasses import dataclass
from itertools import product


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------
class ParseError(Exception):
    """Raised for any syntax error. `position` is a 0-based index into the input."""

    def __init__(self, message, position=None):
        self.message = message
        self.position = position
        where = f" (at position {position})" if position is not None else ""
        super().__init__(f"{message}{where}")


# --------------------------------------------------------------------------
# AST
# --------------------------------------------------------------------------
class Node:
    pass


@dataclass(frozen=True)
class Var(Node):
    name: str


@dataclass(frozen=True)
class Const(Node):
    value: bool


@dataclass(frozen=True)
class Not(Node):
    child: Node


@dataclass(frozen=True)
class And(Node):
    left: Node
    right: Node


@dataclass(frozen=True)
class Or(Node):
    left: Node
    right: Node


@dataclass(frozen=True)
class Implies(Node):
    left: Node
    right: Node


@dataclass(frozen=True)
class Iff(Node):
    left: Node
    right: Node


BINARY = (And, Or, Implies, Iff)


# --------------------------------------------------------------------------
# Tokenizer
# --------------------------------------------------------------------------
# Token kinds
VAR, CONST = "VAR", "CONST"
NOT, AND, OR, IMPLIES, IFF = "NOT", "AND", "OR", "IMPLIES", "IFF"
LPAREN, RPAREN = "LPAREN", "RPAREN"

# Symbol spellings, longest first so "<->" is matched before "->".
SYMBOLS = [
    ("<->", IFF), ("<=>", IFF), ("\u2194", IFF),          # <->  <=>  ↔
    ("->", IMPLIES), ("=>", IMPLIES), ("\u2192", IMPLIES),  # ->  =>  →
    ("&&", AND), ("&", AND), ("\u2227", AND),              # &&  &  ∧
    ("||", OR), ("|", OR), ("\u2228", OR),                 # ||  |  ∨
    ("~", NOT), ("!", NOT), ("\u00ac", NOT),               # ~  !  ¬
    ("(", LPAREN), (")", RPAREN),
]

# Word spellings (case-insensitive).
WORDS = {
    "and": AND, "or": OR, "not": NOT, "implies": IMPLIES, "iff": IFF,
    "true": CONST, "false": CONST,
}


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    pos: int


def tokenize(text):
    """Turn a string into a list of Tokens. Raises ParseError on unknown symbols."""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue

        # Symbols (operators and parentheses)
        for sym, kind in SYMBOLS:
            if text.startswith(sym, i):
                tokens.append(Token(kind, sym, i))
                i += len(sym)
                break
        else:
            # Constants 0 and 1
            if ch in "01":
                tokens.append(Token(CONST, ch, i))
                i += 1
            # Variables and word operators
            elif ch.isalpha() or ch == "_":
                j = i
                while j < n and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                word = text[i:j]
                kind = WORDS.get(word.lower(), VAR)
                tokens.append(Token(kind, word, i))
                i = j
            else:
                raise ParseError(f"Unknown symbol '{ch}'", i)
    return tokens


# --------------------------------------------------------------------------
# Parser (recursive descent)
#
# Grammar, loosest to tightest binding:
#   expr    := iff
#   iff     := implies ( IFF implies )*          left-associative
#   implies := or ( IMPLIES implies )?           right-associative
#   or      := and ( OR and )*                   left-associative
#   and     := not ( AND not )*                  left-associative
#   not     := NOT not | atom
#   atom    := VAR | CONST | LPAREN expr RPAREN
# --------------------------------------------------------------------------
class _Parser:
    def __init__(self, tokens, text):
        self.tokens = tokens
        self.pos = 0
        self.end = len(text)

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def accept(self, kind):
        tok = self.peek()
        if tok is not None and tok.kind == kind:
            self.pos += 1
            return tok
        return None

    def parse(self):
        if not self.tokens:
            raise ParseError("Empty expression", 0)
        node = self.iff()
        tok = self.peek()
        if tok is not None:
            if tok.kind == RPAREN:
                raise ParseError("Unmatched closing parenthesis ')'", tok.pos)
            raise ParseError(f"Unexpected '{tok.text}' (missing operator?)", tok.pos)
        return node

    def iff(self):
        left = self.implies()
        while self.accept(IFF):
            left = Iff(left, self.implies())
        return left

    def implies(self):
        left = self.or_()
        if self.accept(IMPLIES):
            return Implies(left, self.implies())  # right-associative
        return left

    def or_(self):
        left = self.and_()
        while self.accept(OR):
            left = Or(left, self.and_())
        return left

    def and_(self):
        left = self.not_()
        while self.accept(AND):
            left = And(left, self.not_())
        return left

    def not_(self):
        if self.accept(NOT):
            return Not(self.not_())
        return self.atom()

    def atom(self):
        tok = self.peek()
        if tok is None:
            raise ParseError("Expression ended unexpectedly (missing operand)", self.end)
        if tok.kind == VAR:
            self.pos += 1
            return Var(tok.text)
        if tok.kind == CONST:
            self.pos += 1
            return Const(tok.text.lower() in ("1", "true"))
        if tok.kind == LPAREN:
            self.pos += 1
            node = self.iff()
            if not self.accept(RPAREN):
                raise ParseError("Missing closing parenthesis ')'", tok.pos)
            return node
        if tok.kind in (AND, OR, IMPLIES, IFF):
            raise ParseError(f"Operator '{tok.text}' is missing a left operand", tok.pos)
        if tok.kind == RPAREN:
            raise ParseError("Empty or misplaced parentheses", tok.pos)
        raise ParseError(f"Unexpected '{tok.text}'", tok.pos)


def parse(text):
    """Parse a propositional formula string into an AST."""
    return _Parser(tokenize(text), text).parse()


# --------------------------------------------------------------------------
# Printing
# --------------------------------------------------------------------------
_PREC = {Iff: 1, Implies: 2, Or: 3, And: 4, Not: 5, Var: 6, Const: 6}
_SYM = {And: "\u2227", Or: "\u2228", Implies: "\u2192", Iff: "\u2194"}


def to_string(node):
    """Readable formula using the symbols ∧ ∨ ¬ → ↔ and minimal parentheses."""
    if isinstance(node, Var):
        return node.name
    if isinstance(node, Const):
        return "1" if node.value else "0"
    if isinstance(node, Not):
        inner = to_string(node.child)
        if isinstance(node.child, BINARY):
            inner = f"({inner})"
        return "\u00ac" + inner

    prec = _PREC[type(node)]
    left = to_string(node.left)
    right = to_string(node.right)
    lp = _PREC[type(node.left)]
    rp = _PREC[type(node.right)]
    if isinstance(node, Implies):          # right-associative
        if lp <= prec:
            left = f"({left})"
        if rp < prec:
            right = f"({right})"
    else:                                  # left-associative
        if lp < prec:
            left = f"({left})"
        if rp <= prec:
            right = f"({right})"
    return f"{left} {_SYM[type(node)]} {right}"


# --------------------------------------------------------------------------
# Evaluation and truth tables
# --------------------------------------------------------------------------
def variables(node):
    """Variable names in order of first appearance (left to right)."""
    seen = []

    def walk(n):
        if isinstance(n, Var):
            if n.name not in seen:
                seen.append(n.name)
        elif isinstance(n, Not):
            walk(n.child)
        elif isinstance(n, BINARY):
            walk(n.left)
            walk(n.right)

    walk(node)
    return seen


def evaluate(node, assignment):
    """Evaluate under {name: 0/1/bool}. Raises KeyError if a variable is missing."""
    if isinstance(node, Var):
        return bool(assignment[node.name])
    if isinstance(node, Const):
        return node.value
    if isinstance(node, Not):
        return not evaluate(node.child, assignment)
    a = evaluate(node.left, assignment)
    b = evaluate(node.right, assignment)
    if isinstance(node, And):
        return a and b
    if isinstance(node, Or):
        return a or b
    if isinstance(node, Implies):
        return (not a) or b
    if isinstance(node, Iff):
        return a == b
    raise TypeError(f"Unknown node type: {type(node).__name__}")


def truth_table(node, names=None):
    """
    Full truth table as a list of dict rows, e.g.
        {"p": 1, "q": 0, "result": 0}
    Rows follow standard order (all 1s first, as in textbooks).
    """
    names = names if names is not None else variables(node)
    rows = []
    for values in product([1, 0], repeat=len(names)):
        assignment = dict(zip(names, values))
        row = dict(assignment)
        row["result"] = int(evaluate(node, assignment))
        rows.append(row)
    return rows


def format_truth_table(node):
    """Plain-text truth table for printing or reports."""
    names = variables(node)
    header = names + [to_string(node)]
    widths = [max(len(h), 1) for h in header]
    lines = [" | ".join(h.center(w) for h, w in zip(header, widths))]
    lines.append("-+-".join("-" * w for w in widths))
    for row in truth_table(node, names):
        cells = [str(row[n]) for n in names] + [str(row["result"])]
        lines.append(" | ".join(c.center(w) for c, w in zip(cells, widths)))
    return "\n".join(lines)


def equivalent(a, b):
    """True if two formulas have identical truth tables over all their variables."""
    names = variables(a) + [v for v in variables(b) if v not in variables(a)]
    for values in product([1, 0], repeat=len(names)):
        env = dict(zip(names, values))
        if evaluate(a, env) != evaluate(b, env):
            return False
    return True


# --------------------------------------------------------------------------
# Rewriting engine (simplification and De Morgan), with a step log
# --------------------------------------------------------------------------
def _step(node, rewrite):
    """Apply one rewrite at the leftmost-innermost place possible, else None."""
    if isinstance(node, Not):
        r = _step(node.child, rewrite)
        if r:
            return Not(r[0]), r[1]
    elif isinstance(node, BINARY):
        r = _step(node.left, rewrite)
        if r:
            return type(node)(r[0], node.right), r[1]
        r = _step(node.right, rewrite)
        if r:
            return type(node)(node.left, r[0]), r[1]
    return rewrite(node)


def _run(node, rewrite, keep_going=True, limit=1000):
    steps = []
    for _ in range(limit):
        r = _step(node, rewrite)
        if r is None:
            break
        node, law = r
        steps.append((law, to_string(node)))
    return node, steps


def _rewrite_simplify(n):
    """One-step rewrites for eliminating → / ↔ and for Boolean-algebra laws."""
    # Eliminate implication and biconditional so only AND/OR/NOT remain.
    if isinstance(n, Implies):
        return Or(Not(n.left), n.right), "Implication: p \u2192 q \u2261 \u00acp \u2228 q"
    if isinstance(n, Iff):
        return (And(Or(Not(n.left), n.right), Or(Not(n.right), n.left)),
                "Biconditional: p \u2194 q \u2261 (\u00acp \u2228 q) \u2227 (\u00acq \u2228 p)")

    if isinstance(n, Not):
        c = n.child
        if isinstance(c, Not):
            return c.child, "Double negation: \u00ac\u00acp \u2261 p"
        if isinstance(c, Const):
            return Const(not c.value), "Negation of a constant"

    if isinstance(n, (And, Or)):
        is_and = isinstance(n, And)
        l, r = n.left, n.right
        identity = Const(is_and)        # p \u2227 1 = p ;  p \u2228 0 = p
        dominator = Const(not is_and)   # p \u2227 0 = 0 ;  p \u2228 1 = 1
        if l == identity:
            return r, "Identity law"
        if r == identity:
            return l, "Identity law"
        if l == dominator or r == dominator:
            return dominator, "Domination law"
        if l == r:
            return l, "Idempotent law: p \u2227 p \u2261 p" if is_and else "Idempotent law: p \u2228 p \u2261 p"
        if l == Not(r) or r == Not(l):
            return dominator, "Complement (negation) law"
        # Repeats inside a chain: (q ∧ p) ∧ p  ≡  q ∧ p   (idempotent + associative)
        same = And if is_and else Or
        if isinstance(l, same) and (r == l.left or r == l.right):
            return l, "Idempotent law (with associativity)"
        if isinstance(r, same) and (l == r.left or l == r.right):
            return r, "Idempotent law (with associativity)"
        other = Or if is_and else And
        for a, b in ((l, r), (r, l)):
            if isinstance(b, other) and (a == b.left or a == b.right):
                return a, "Absorption law"
    return None


def _rewrite_de_morgan(n):
    if isinstance(n, Not):
        c = n.child
        if isinstance(c, And):
            return Or(Not(c.left), Not(c.right)), "De Morgan: \u00ac(p \u2227 q) \u2261 \u00acp \u2228 \u00acq"
        if isinstance(c, Or):
            return And(Not(c.left), Not(c.right)), "De Morgan: \u00ac(p \u2228 q) \u2261 \u00acp \u2227 \u00acq"
        if isinstance(c, Not):
            return c.child, "Double negation: \u00ac\u00acp \u2261 p"
    return None


def simplify(node):
    """
    Eliminate → and ↔, then apply identity, domination, idempotent, complement,
    double-negation and absorption laws until nothing changes.

    Returns (simplified_node, steps) where steps is a list of
    (law_name, expression_after_the_step) for use as a derivation in the report.
    The result only uses AND, OR and NOT, ready for circuit generation.
    """
    return _run(node, _rewrite_simplify)


def to_nnf(node):
    """Negation normal form: apply De Morgan's laws so ¬ only sits on variables."""
    node, steps1 = _run(node, _rewrite_simplify_elimination_only)
    node, steps2 = _run(node, _rewrite_de_morgan)
    return node, steps1 + steps2


def _rewrite_simplify_elimination_only(n):
    if isinstance(n, (Implies, Iff)):
        return _rewrite_simplify(n)
    return None


# --------------------------------------------------------------------------
# Convenience: full pipeline in one call
# --------------------------------------------------------------------------
def analyse(text):
    """
    Parse, simplify and tabulate a formula.
    Returns a dict:
        ast, simplified, steps, variables, table, verified
    `verified` is True when the simplified formula is truth-table equivalent
    to the original (this should always hold).
    """
    ast = parse(text)
    simp, steps = simplify(ast)
    return {
        "ast": ast,
        "simplified": simp,
        "steps": steps,
        "variables": variables(ast),
        "table": truth_table(ast),
        "verified": equivalent(ast, simp),
    }


# --------------------------------------------------------------------------
# Command-line demo
# --------------------------------------------------------------------------
def _show(text):
    try:
        info = analyse(text)
    except ParseError as e:
        print(f"  Error: {e}")
        if e.position is not None:
            print("  " + text)
            print("  " + " " * e.position + "^")
        return
    print(f"  Parsed:     {to_string(info['ast'])}")
    print(f"  Variables:  {', '.join(info['variables']) or '(none)'}")
    print("  Simplification steps:")
    if info["steps"]:
        for law, expr in info["steps"]:
            print(f"    {law:<55} => {expr}")
    else:
        print("    (nothing to simplify)")
    print(f"  Simplified: {to_string(info['simplified'])}")
    print(f"  Equivalent to original: {info['verified']}")
    print()
    print(format_truth_table(info["ast"]))


if __name__ == "__main__":
    print("Logic Engine - enter a propositional formula (blank line to quit).")
    print("Operators: ¬ ~ ! NOT | ∧ & AND | ∨ | OR | → -> IMPLIES | ↔ <-> IFF")
    while True:
        try:
            line = input("\nformula> ").strip()
        except EOFError:
            break
        if not line:
            break
        _show(line)