"""Subset construction: NFA → DFA for a faster matcher path."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .nfa import EPSILON, NFA, epsilon_closure, move


@dataclass
class DFA:
    # state id → (char → next state id); missing char means reject
    transitions: Dict[int, Dict[str, int]]
    # also keep a "any" (dot / class) handler via fallback function per state
    # for simplicity we expand on the alphabet we actually see, plus a
    # wildcard table for labels that aren't plain chars
    start: int
    accepts: Set[int]
    # for labels that aren't single chars we keep predicate transitions
    predicates: Dict[int, List[Tuple[object, int]]] = field(default_factory=dict)
    state_count: int = 0
    pattern: str = ""


def _collect_labels(nfa: NFA, state_set: Set[int]) -> Set[Optional[str]]:
    labels: Set[Optional[str]] = set()
    for sid in state_set:
        for label in nfa.states[sid].edges:
            if label is not EPSILON:
                labels.add(label)
    return labels


def _chars_for_label(nfa: NFA, sid_set: Set[int], label: str) -> Optional[Set[str]]:
    """If label is a concrete char, return {char}; else None (predicate)."""
    if label == "." or label.startswith("[[:class:"):
        return None
    return {label}


def compile_dfa(nfa: NFA) -> DFA:
    """Powerset construction. Alphabet is discovered from NFA edge labels;
    non-char labels (dot, classes) become predicate transitions."""
    start_set = frozenset(epsilon_closure(nfa, {nfa.start}))
    state_map: Dict[frozenset, int] = {start_set: 0}
    work: List[frozenset] = [start_set]
    transitions: Dict[int, Dict[str, int]] = {0: {}}
    predicates: Dict[int, List[Tuple[object, int]]] = {0: []}
    accepts: Set[int] = set()
    if nfa.accept in start_set:
        accepts.add(0)

    def get_id(sset: frozenset) -> int:
        if sset not in state_map:
            nid = len(state_map)
            state_map[sset] = nid
            transitions[nid] = {}
            predicates[nid] = []
            work.append(sset)
            if nfa.accept in sset:
                accepts.add(nid)
        return state_map[sset]

    while work:
        current = work.pop()
        cid = state_map[current]
        labels = _collect_labels(nfa, set(current))

        # group concrete char labels
        char_targets: Dict[str, Set[int]] = {}
        pred_list: List[Tuple[object, frozenset]] = []

        for label in labels:
            if label is None:
                continue
            # compute move on this symbolic label by synthesizing a probe char
            # for concrete chars we can just step; for predicates we store them
            chars = _chars_for_label(nfa, set(current), label)
            if chars is not None:
                for ch in chars:
                    nxt = epsilon_closure(nfa, move(nfa, set(current), ch))
                    if nxt:
                        char_targets.setdefault(ch, set()).update(nxt)
            else:
                # predicate: store a callable that tests the char
                def make_pred(lab: str, sids: frozenset):
                    def pred(ch: str) -> bool:
                        # would any state in sids fire on ch via lab?
                        from .nfa import _edge_matches

                        for sid in sids:
                            for L, _tgts in nfa.states[sid].edges.items():
                                if L == lab and _edge_matches(nfa, sid, L, ch):
                                    return True
                        return False

                    return pred

                # compute destination by trying all states' move for that label
                # We need the set of targets when the predicate matches.
                # Collect targets directly from edges with this label.
                dest: Set[int] = set()
                for sid in current:
                    for L, tgts in nfa.states[sid].edges.items():
                        if L == label:
                            dest.update(tgts)
                dest_closed = frozenset(epsilon_closure(nfa, dest))
                if dest_closed:
                    pred_list.append((make_pred(label, current), dest_closed))

        for ch, dest in char_targets.items():
            nid = get_id(frozenset(dest))
            transitions[cid][ch] = nid

        for pred, dest_closed in pred_list:
            nid = get_id(dest_closed)
            predicates[cid].append((pred, nid))

    return DFA(
        transitions=transitions,
        start=0,
        accepts=accepts,
        predicates=predicates,
        state_count=len(state_map),
        pattern=nfa.pattern,
    )


def _step(dfa: DFA, state: int, ch: str) -> Optional[int]:
    trans = dfa.transitions.get(state, {})
    if ch in trans:
        return trans[ch]
    for pred, nxt in dfa.predicates.get(state, []):
        if pred(ch):
            return nxt
    return None


def dfa_fullmatch(dfa: DFA, text: str) -> bool:
    state: Optional[int] = dfa.start
    for ch in text:
        if state is None:
            return False
        state = _step(dfa, state, ch)
    return state is not None and state in dfa.accepts


def dfa_search(dfa: DFA, text: str) -> Optional[Tuple[int, int]]:
    n = len(text)
    for i in range(n + 1):
        state: Optional[int] = dfa.start
        last: Optional[int] = i if state in dfa.accepts else None
        j = i
        while j < n and state is not None:
            state = _step(dfa, state, text[j])
            j += 1
            if state is not None and state in dfa.accepts:
                last = j
        if last is not None:
            return i, last
    return None
