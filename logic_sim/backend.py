"""
The facade: the ONE place where the UI (Member 3) meets the engine
(Members 1 and 2).

The UI only ever imports this file, never parsing/ or circuit/ directly.
That keeps the three parts independent.

While Members 1 and 2 are still working, USE_MOCK = True makes the UI run on
fake data from mock_backend.py. When both modules are ready, set it to False.
"""

USE_MOCK = True

if USE_MOCK:
    from logic_sim.mock_backend import get_circuit, get_truth_table, propagate
else:
    from logic_sim.circuit import build_circuit, propagate
    from logic_sim.parsing import parse
    from logic_sim.parsing import truth_table as _truth_table

    def get_circuit(expression):
        """expression string -> circuit graph (raises ValueError on bad input)."""
        return build_circuit(parse(expression))

    def get_truth_table(expression):
        """expression string -> truth table (raises ValueError on bad input)."""
        return _truth_table(parse(expression))
