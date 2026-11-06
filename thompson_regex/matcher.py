"""NFA simulation: match / search / findall."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from .nfa import NFA, compile_nfa, epsilon_closure, move


@dataclass
class Match:
    start: int
    end: int
    text: str

    @property
    def span(self) -> Tuple[int, int]:
        return self.start, self.end

    def group(self) -> str:
        return self.text[self.start : self.end]

    def __repr__(self) -> str:
        return f"<Match span={self.span} match={self.group()!r}>"


class Pattern:
    """Compiled regex. Prefer the package-level compile()."""

    def __init__(self, pattern: str, nfa: Optional[NFA] = None, use_dfa: bool = False):
        self.pattern = pattern
        self.nfa = nfa or compile_nfa(pattern)
        self._dfa = None
        self.use_dfa = use_dfa
        if use_dfa:
            from .dfa import compile_dfa

            self._dfa = compile_dfa(self.nfa)

    def match(self, text: str) -> Optional[Match]:
        """Full-string match (like re.fullmatch)."""
        if self._dfa is not None:
            from .dfa import dfa_fullmatch

            if dfa_fullmatch(self._dfa, text):
                return Match(0, len(text), text)
            return None
        return self._nfa_fullmatch(text)

    def search(self, text: str) -> Optional[Match]:
        """Leftmost match anywhere in the string."""
        if self._dfa is not None:
            from .dfa import dfa_search

            span = dfa_search(self._dfa, text)
            if span is None:
                return None
            return Match(span[0], span[1], text)
        return self._nfa_search(text)

    def findall(self, text: str) -> List[str]:
        return [m.group() for m in self.finditer(text)]

    def finditer(self, text: str) -> List[Match]:
        results: List[Match] = []
        pos = 0
        n = len(text)
        while pos <= n:
            m = self._nfa_search_from(text, pos)
            if m is None:
                break
            results.append(m)
            # advance at least one char to avoid infinite empty matches
            pos = m.end if m.end > m.start else m.end + 1
        return results

    # --- NFA engine ----------------------------------------------------------

    def _nfa_fullmatch(self, text: str) -> Optional[Match]:
        states = epsilon_closure(self.nfa, {self.nfa.start})
        for ch in text:
            states = epsilon_closure(self.nfa, move(self.nfa, states, ch))
            if not states:
                return None
        if self.nfa.accept in states:
            return Match(0, len(text), text)
        return None

    def _nfa_search(self, text: str) -> Optional[Match]:
        return self._nfa_search_from(text, 0)

    def _nfa_search_from(self, text: str, start: int) -> Optional[Match]:
        """Leftmost-longest search starting at or after `start`."""
        n = len(text)
        for i in range(start, n + 1):
            m = self._nfa_match_at(text, i)
            if m is not None:
                return m
        return None

    def _nfa_match_at(self, text: str, start: int) -> Optional[Match]:
        """Longest match beginning at `start` (or None)."""
        states = epsilon_closure(self.nfa, {self.nfa.start})
        last_accept: Optional[int] = None
        if self.nfa.accept in states:
            last_accept = start
        i = start
        n = len(text)
        while i < n and states:
            states = epsilon_closure(self.nfa, move(self.nfa, states, text[i]))
            i += 1
            if self.nfa.accept in states:
                last_accept = i
        if last_accept is None:
            return None
        return Match(start, last_accept, text)


def compile(pattern: str, use_dfa: bool = False) -> Pattern:
    return Pattern(pattern, use_dfa=use_dfa)
