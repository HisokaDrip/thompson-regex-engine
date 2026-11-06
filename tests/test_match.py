import pytest

from thompson_regex import compile
from thompson_regex.parser import RegexSyntaxError


def test_fullmatch_basic():
    rx = compile("abc")
    assert rx.match("abc") is not None
    assert rx.match("ab") is None
    assert rx.match("abcd") is None


def test_alternation():
    rx = compile("foo|bar|baz")
    assert rx.match("foo") and rx.match("bar") and rx.match("baz")
    assert rx.match("qux") is None


def test_quantifiers():
    assert compile("a*").match("") is not None
    assert compile("a*").match("aaa") is not None
    assert compile("a+").match("") is None
    assert compile("a+").match("a") is not None
    assert compile("a?").match("") is not None
    assert compile("a?").match("a") is not None
    assert compile("a?").match("aa") is None


def test_concat_and_group():
    rx = compile("a(b|c)+d")
    assert rx.match("abd") and rx.match("acccd")
    assert rx.match("ad") is None
    assert rx.match("ab") is None


def test_dot():
    rx = compile("a.b")
    assert rx.match("axb") and rx.match("a b")
    assert rx.match("ab") is None
    assert rx.match("a\nb") is None


def test_char_classes():
    assert compile("[a-z]+").match("hello")
    assert compile("[a-z]+").match("Hello") is None
    assert compile(r"\d+").match("90210")
    assert compile(r"\w+").match("var_1")
    assert compile(r"\s+").match(" \t")
    assert compile("[^a-z]+").match("123")
    assert compile("[^a-z]+").match("abc") is None


def test_search():
    rx = compile("cat|dog")
    m = rx.search("the dog ran")
    assert m is not None
    assert m.group() == "dog"
    assert m.span == (4, 7)
    assert rx.search("bird") is None


def test_findall():
    rx = compile("a+")
    assert rx.findall("xaaayaaa") == ["aaa", "aaa"]
    assert compile("z").findall("abc") == []


def test_leftmost_longest():
    # both 'a' and 'ab' can start a match; prefer longer when starting at 0
    rx = compile("a|ab")
    m = rx.match("ab")
    # NFA explores both; longest accept wins for match-at
    assert m is not None
    assert m.group() in ("a", "ab")  # either branch ok for alt at same start
    # for (a|ab)c the longer branch is needed
    rx2 = compile("(a|ab)c")
    assert rx2.match("abc").group() == "abc"
    assert rx2.match("ac").group() == "ac"


def test_colour():
    rx = compile("colou?r")
    assert rx.match("color") and rx.match("colour")
    assert rx.match("colouur") is None


def test_compile_bad_pattern():
    with pytest.raises(RegexSyntaxError):
        compile("(")
