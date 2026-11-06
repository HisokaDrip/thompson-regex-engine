"""Thompson-construction regex engine.

Parse a small regex subset into an AST, compile to an NFA (Thompson),
optionally determinize to a DFA, then match / search / findall.
"""

from .matcher import Match, Pattern, compile
from .nfa import NFA, compile_nfa
from .parser import RegexSyntaxError, parse
from .dfa import compile_dfa

__all__ = [
    "compile",
    "compile_nfa",
    "compile_dfa",
    "parse",
    "Match",
    "Pattern",
    "NFA",
    "RegexSyntaxError",
]

__version__ = "0.1.0"
