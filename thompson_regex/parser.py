"""Regex subset → AST.

Supported: literals, `.`, `*`, `+`, `?`, `|`, `()`, character classes
(`[a-z]`, `[0-9]`, `[^...]`), and common backslash escapes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set, Union


class RegexSyntaxError(ValueError):
    pass


# --- AST nodes ---------------------------------------------------------------

@dataclass(frozen=True)
class Literal:
    char: str


@dataclass(frozen=True)
class Dot:
    pass


@dataclass(frozen=True)
class CharClass:
    chars: frozenset
    negated: bool = False


@dataclass(frozen=True)
class Concat:
    left: "Node"
    right: "Node"


@dataclass(frozen=True)
class Alt:
    left: "Node"
    right: "Node"


@dataclass(frozen=True)
class Star:
    node: "Node"


@dataclass(frozen=True)
class Plus:
    node: "Node"


@dataclass(frozen=True)
class Question:
    node: "Node"


Node = Union[Literal, Dot, CharClass, Concat, Alt, Star, Plus, Question]

DIGIT = frozenset("0123456789")
WORD = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
SPACE = frozenset(" \t\n\r\f\v")


def _escape_char(c: str) -> CharClass | Literal:
    if c == "d":
        return CharClass(DIGIT)
    if c == "w":
        return CharClass(WORD)
    if c == "s":
        return CharClass(SPACE)
    if c == "D":
        return CharClass(DIGIT, negated=True)
    if c == "W":
        return CharClass(WORD, negated=True)
    if c == "S":
        return CharClass(SPACE, negated=True)
    if c == "n":
        return Literal("\n")
    if c == "t":
        return Literal("\t")
    if c == "r":
        return Literal("\r")
    # literal escape of the character itself
    return Literal(c)


class Parser:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.i = 0

    def parse(self) -> Node:
        if not self.pattern:
            raise RegexSyntaxError("empty pattern")
        node = self._parse_alt()
        if self.i < len(self.pattern):
            raise RegexSyntaxError(
                f"unexpected character {self.pattern[self.i]!r} at position {self.i}"
            )
        return node

    def _peek(self) -> Optional[str]:
        if self.i < len(self.pattern):
            return self.pattern[self.i]
        return None

    def _advance(self) -> str:
        c = self.pattern[self.i]
        self.i += 1
        return c

    def _parse_alt(self) -> Node:
        left = self._parse_concat()
        while self._peek() == "|":
            self._advance()
            right = self._parse_concat()
            left = Alt(left, right)
        return left

    def _parse_concat(self) -> Node:
        parts: List[Node] = []
        while True:
            c = self._peek()
            if c is None or c in ")|":
                break
            parts.append(self._parse_quantified())
        if not parts:
            raise RegexSyntaxError(f"expected atom at position {self.i}")
        node = parts[0]
        for p in parts[1:]:
            node = Concat(node, p)
        return node

    def _parse_quantified(self) -> Node:
        atom = self._parse_atom()
        c = self._peek()
        if c == "*":
            self._advance()
            return Star(atom)
        if c == "+":
            self._advance()
            return Plus(atom)
        if c == "?":
            self._advance()
            return Question(atom)
        return atom

    def _parse_atom(self) -> Node:
        c = self._peek()
        if c is None:
            raise RegexSyntaxError("unexpected end of pattern")
        if c == "(":
            self._advance()
            inner = self._parse_alt()
            if self._peek() != ")":
                raise RegexSyntaxError(f"unclosed group at position {self.i}")
            self._advance()
            return inner
        if c == "[":
            return self._parse_class()
        if c == ".":
            self._advance()
            return Dot()
        if c == "\\":
            self._advance()
            esc = self._peek()
            if esc is None:
                raise RegexSyntaxError("trailing backslash")
            self._advance()
            return _escape_char(esc)
        if c in "*+?|)":
            raise RegexSyntaxError(f"unexpected {c!r} at position {self.i}")
        self._advance()
        return Literal(c)

    def _parse_class(self) -> CharClass:
        # caller sees '['
        self._advance()
        negated = False
        if self._peek() == "^":
            self._advance()
            negated = True
        chars: Set[str] = set()
        if self._peek() is None:
            raise RegexSyntaxError("unclosed character class")
        # first char can be ] or - literally
        first = True
        while True:
            c = self._peek()
            if c is None:
                raise RegexSyntaxError("unclosed character class")
            if c == "]" and not first:
                self._advance()
                break
            first = False
            if c == "\\":
                self._advance()
                esc = self._peek()
                if esc is None:
                    raise RegexSyntaxError("trailing backslash in class")
                self._advance()
                node = _escape_char(esc)
                if isinstance(node, CharClass):
                    chars |= set(node.chars)
                else:
                    chars.add(node.char)
                continue
            self._advance()
            # range a-z
            if self._peek() == "-" and self.i + 1 < len(self.pattern) and self.pattern[self.i + 1] != "]":
                self._advance()  # skip '-'
                end = self._peek()
                if end is None:
                    raise RegexSyntaxError("unclosed character class")
                if end == "\\":
                    self._advance()
                    esc = self._peek()
                    if esc is None:
                        raise RegexSyntaxError("trailing backslash in class")
                    self._advance()
                    node = _escape_char(esc)
                    end = node.char if isinstance(node, Literal) else esc
                else:
                    self._advance()
                if ord(c) > ord(end):
                    raise RegexSyntaxError(f"bad range {c}-{end}")
                for code in range(ord(c), ord(end) + 1):
                    chars.add(chr(code))
            else:
                chars.add(c)
        return CharClass(frozenset(chars), negated=negated)


def parse(pattern: str) -> Node:
    return Parser(pattern).parse()
