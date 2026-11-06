import pytest

from thompson_regex.parser import (
    Alt,
    CharClass,
    Concat,
    Dot,
    Literal,
    Plus,
    Question,
    RegexSyntaxError,
    Star,
    parse,
)


def test_literal():
    n = parse("a")
    assert isinstance(n, Literal) and n.char == "a"


def test_concat_vs_alt_precedence():
    # ab|cd  =>  (ab)|(cd), not a(b|c)d
    n = parse("ab|cd")
    assert isinstance(n, Alt)
    assert isinstance(n.left, Concat)
    assert isinstance(n.right, Concat)
    assert n.left.left.char == "a"
    assert n.left.right.char == "b"


def test_quantifier_binds_tight():
    n = parse("ab*")
    assert isinstance(n, Concat)
    assert isinstance(n.right, Star)
    assert isinstance(n.right.node, Literal)


def test_nested_groups():
    n = parse("a(b|c)+")
    assert isinstance(n, Concat)
    assert isinstance(n.right, Plus)
    assert isinstance(n.right.node, Alt)


def test_dot_and_question():
    n = parse("a.?")
    assert isinstance(n, Concat)
    assert isinstance(n.right, Question)
    assert isinstance(n.right.node, Dot)


def test_char_class_range():
    n = parse("[a-c]")
    assert isinstance(n, CharClass)
    assert n.chars == frozenset("abc")
    assert not n.negated


def test_negated_class():
    n = parse("[^0-9]")
    assert isinstance(n, CharClass) and n.negated
    assert "5" in n.chars


def test_escape_classes():
    n = parse(r"\d")
    assert isinstance(n, CharClass)
    assert "7" in n.chars


def test_rejects_empty():
    with pytest.raises(RegexSyntaxError):
        parse("")


@pytest.mark.parametrize(
    "bad",
    ["(", ")", "*", "+", "?", "|a", "a|", "a)", "[abc", "\\", "a**"],
)
def test_rejects_invalid(bad):
    with pytest.raises(RegexSyntaxError):
        parse(bad)
