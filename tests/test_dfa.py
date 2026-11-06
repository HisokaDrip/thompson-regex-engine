import pytest

from thompson_regex import compile, compile_dfa, compile_nfa


PATTERNS = [
    "a",
    "ab",
    "a*",
    "a+",
    "a?",
    "a|b",
    "a(b|c)",
    "a*b",
    "(ab)+",
    r"\d+",
    "[a-z]+",
    "colou?r",
    "a(b|c)*d",
]


@pytest.mark.parametrize("pat", PATTERNS)
@pytest.mark.parametrize(
    "text",
    ["", "a", "b", "ab", "ba", "abc", "aab", "123", "colour", "color", "axd", "acccd"],
)
def test_dfa_matches_nfa(pat, text):
    nfa_rx = compile(pat, use_dfa=False)
    dfa_rx = compile(pat, use_dfa=True)
    nfa_hit = nfa_rx.match(text) is not None
    dfa_hit = dfa_rx.match(text) is not None
    assert nfa_hit == dfa_hit, f"{pat!r} on {text!r}: nfa={nfa_hit} dfa={dfa_hit}"


def test_dfa_state_count_shrinks():
    nfa = compile_nfa("a*b|c")
    dfa = compile_dfa(nfa)
    assert dfa.state_count >= 1
    # DFA should not explode on this tiny pattern
    assert dfa.state_count <= nfa.state_count + 2


def test_dfa_search():
    rx = compile(r"\d+", use_dfa=True)
    m = rx.search("id=42;")
    assert m is not None and m.group() == "42"


def test_dfa_fullmatch_reject():
    rx = compile("abc", use_dfa=True)
    assert rx.match("ab") is None
    assert rx.match("abcd") is None
