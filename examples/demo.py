"""Small demo: match a few patterns and show NFA / DFA sizes."""

from thompson_regex import compile, compile_dfa, compile_nfa


SAMPLES = [
    ("a*b", ["b", "aaab", "aaa"]),
    ("a(b|c)+", ["ab", "acbbc", "a", "ax"]),
    (r"\d+\.\d+", ["3.14", "0.0", "42", "3."]),
    ("colou?r", ["color", "colour", "colouur"]),
    ("(ab|a)c", ["abc", "ac", "ab"]),
]


def main() -> None:
    print("=== matches ===")
    for pat, texts in SAMPLES:
        rx = compile(pat)
        print(f"\npattern: {pat!r}")
        for t in texts:
            m = rx.match(t)
            print(f"  match({t!r}) -> {m.group()!r}" if m else f"  match({t!r}) -> None")

    print("\n=== search / findall ===")
    rx = compile("cat|dog|bird")
    text = "the dog chased the cat past a bird"
    print(f"search({text!r}) -> {rx.search(text)!r}")
    print(f"findall(...) -> {rx.findall(text)}")

    print("\n=== NFA / DFA state counts ===")
    print(f"{'pattern':<20} {'NFA':>5} {'DFA':>5}")
    for pat in [
        "a",
        "a*b",
        "a|b",
        "(ab)+",
        r"\w+",
        "[a-z][0-9]?",
        "a(b|c)*d",
        "colou?r",
        r"\d+\.\d+",
    ]:
        nfa = compile_nfa(pat)
        dfa = compile_dfa(nfa)
        print(f"{pat:<20} {nfa.state_count:5d} {dfa.state_count:5d}")


if __name__ == "__main__":
    main()
