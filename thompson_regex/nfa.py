"""Thompson construction: AST → NFA with ε-transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .parser import (
    Alt,
    CharClass,
    Concat,
    DIGIT,
    Dot,
    Literal,
    Node,
    Plus,
    Question,
    SPACE,
    Star,
    WORD,
    parse,
)

EPSILON = None  # None label means ε


@dataclass
class State:
    id: int
    # label → list of target state ids; EPSILON key is None
    edges: Dict[Optional[str], List[int]] = field(default_factory=dict)

    def add(self, label: Optional[str], target: int) -> None:
        self.edges.setdefault(label, []).append(target)


@dataclass
class Fragment:
    start: int
    accept: int


@dataclass
class NFA:
    states: List[State]
    start: int
    accept: int
    # for debugging / demos
    pattern: str = ""

    @property
    def state_count(self) -> int:
        return len(self.states)


class Builder:
    def __init__(self):
        self.states: List[State] = []

    def new_state(self) -> int:
        sid = len(self.states)
        self.states.append(State(id=sid))
        return sid

    def build(self, node: Node) -> Fragment:
        if isinstance(node, Literal):
            return self._literal(node.char)
        if isinstance(node, Dot):
            return self._dot()
        if isinstance(node, CharClass):
            return self._char_class(node)
        if isinstance(node, Concat):
            return self._concat(node)
        if isinstance(node, Alt):
            return self._alt(node)
        if isinstance(node, Star):
            return self._star(node)
        if isinstance(node, Plus):
            return self._plus(node)
        if isinstance(node, Question):
            return self._question(node)
        raise TypeError(f"unknown node {type(node)}")

    def _literal(self, char: str) -> Fragment:
        s = self.new_state()
        a = self.new_state()
        self.states[s].add(char, a)
        return Fragment(s, a)

    def _dot(self) -> Fragment:
        # special label '.' means any single char (handled in matcher)
        s = self.new_state()
        a = self.new_state()
        self.states[s].add(".", a)
        return Fragment(s, a)

    def _char_class(self, node: CharClass) -> Fragment:
        # encode as a special label that the matcher expands
        # we store a unique marker string; matcher looks it up via side table
        s = self.new_state()
        a = self.new_state()
        label = f"[[:class:{len(self.states)}:]]"
        self.states[s].add(label, a)
        # stash class info on the state for the matcher
        self.states[s]._char_class = node  # type: ignore[attr-defined]
        return Fragment(s, a)

    def _concat(self, node: Concat) -> Fragment:
        left = self.build(node.left)
        right = self.build(node.right)
        self.states[left.accept].add(EPSILON, right.start)
        return Fragment(left.start, right.accept)

    def _alt(self, node: Alt) -> Fragment:
        left = self.build(node.left)
        right = self.build(node.right)
        s = self.new_state()
        a = self.new_state()
        self.states[s].add(EPSILON, left.start)
        self.states[s].add(EPSILON, right.start)
        self.states[left.accept].add(EPSILON, a)
        self.states[right.accept].add(EPSILON, a)
        return Fragment(s, a)

    def _star(self, node: Star) -> Fragment:
        inner = self.build(node.node)
        s = self.new_state()
        a = self.new_state()
        self.states[s].add(EPSILON, inner.start)
        self.states[s].add(EPSILON, a)
        self.states[inner.accept].add(EPSILON, inner.start)
        self.states[inner.accept].add(EPSILON, a)
        return Fragment(s, a)

    def _plus(self, node: Plus) -> Fragment:
        # one or more = concat(inner, star(inner)) but share one copy
        inner = self.build(node.node)
        s = self.new_state()
        a = self.new_state()
        self.states[s].add(EPSILON, inner.start)
        self.states[inner.accept].add(EPSILON, inner.start)
        self.states[inner.accept].add(EPSILON, a)
        return Fragment(s, a)

    def _question(self, node: Question) -> Fragment:
        inner = self.build(node.node)
        s = self.new_state()
        a = self.new_state()
        self.states[s].add(EPSILON, inner.start)
        self.states[s].add(EPSILON, a)
        self.states[inner.accept].add(EPSILON, a)
        return Fragment(s, a)


def compile_nfa(pattern: str) -> NFA:
    ast = parse(pattern)
    b = Builder()
    frag = b.build(ast)
    return NFA(states=b.states, start=frag.start, accept=frag.accept, pattern=pattern)


def epsilon_closure(nfa: NFA, states: Set[int]) -> Set[int]:
    stack = list(states)
    closure = set(states)
    while stack:
        sid = stack.pop()
        for nxt in nfa.states[sid].edges.get(EPSILON, []):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure


def _edge_matches(nfa: NFA, sid: int, label: Optional[str], ch: str) -> bool:
    if label is None:
        return False
    if label == ".":
        return ch != "\n"
    if label.startswith("[[:class:"):
        cc = getattr(nfa.states[sid], "_char_class", None)
        if cc is None:
            return False
        in_set = ch in cc.chars
        return (not in_set) if cc.negated else in_set
    return label == ch


def move(nfa: NFA, states: Set[int], ch: str) -> Set[int]:
    """States reachable on consuming `ch` (no ε yet)."""
    result: Set[int] = set()
    for sid in states:
        st = nfa.states[sid]
        for label, targets in st.edges.items():
            if label is EPSILON:
                continue
            if _edge_matches(nfa, sid, label, ch):
                result.update(targets)
    return result
