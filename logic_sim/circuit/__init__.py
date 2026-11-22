"""Convert logic ASTs into circuits and simulate their signals."""
from .builder import build_circuit
from .simulation import propagate

__all__ = ["build_circuit", "propagate"]
