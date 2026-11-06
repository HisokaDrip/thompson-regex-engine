# thompson-regex-engine

A small regular-expression engine written from scratch in pure Python. It
parses a regex subset into an AST, builds an NFA with Thompson's construction,
and matches by ε-closure simulation. There is also an optional NFA→DFA path
via subset construction.

Supported syntax: literals, `.`, `*`, `+`, `?`, `|`, parentheses, character
classes (`[a-z]`, `[^0-9]`), and escapes (`\d`, `\w`, `\s`, `\n`, `\t`, …).

## Layout

```
thompson_regex/
  parser.py    # pattern → AST
  nfa.py       # AST → NFA (Thompson)
  matcher.py   # NFA simulation (match / search / findall)
  dfa.py       # subset construction + DFA matcher
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pytest only; engine is stdlib
```

## Library usage

```python
from thompson_regex import compile

rx = compile(r"a(b|c)+")
print(rx.match("acbbc"))          # <Match span=(0, 5) match='acbbc'>
print(rx.search("xxabcyy"))       # <Match span=(2, 5) match='abc'>
print(compile(r"\d+").findall("a1 b22 c"))  # ['1', '22']

# optional DFA path
rx = compile(r"[a-z]+", use_dfa=True)
```

## CLI

```bash
PYTHONPATH=. python -m thompson_regex 'cat|dog' some.txt
PYTHONPATH=. python -m thompson_regex --dfa r'\d+' some.txt
```

## Example output

From `PYTHONPATH=. python examples/demo.py`:

```
=== matches ===

pattern: 'a*b'
  match('b') -> 'b'
  match('aaab') -> 'aaab'
  match('aaa') -> None

pattern: 'a(b|c)+'
  match('ab') -> 'ab'
  match('acbbc') -> 'acbbc'
  match('a') -> None
  match('ax') -> None

pattern: '\\d+\\.\\d+'
  match('3.14') -> '3.14'
  match('0.0') -> '0.0'
  match('42') -> None
  match('3.') -> None

=== search / findall ===
search('the dog chased the cat past a bird') -> <Match span=(4, 7) match='dog'>
findall(...) -> ['dog', 'cat', 'bird']

=== NFA / DFA state counts ===
pattern                NFA   DFA
a                        2     2
a*b                      6     3
a|b                      6     3
(ab)+                    6     3
\w+                      4     2
[a-z][0-9]?              6     3
a(b|c)*d                12     5
colou?r                 14     7
\d+\.\d+                10     4
```

## Tests

```bash
PYTHONPATH=. pytest -q
```

## What I'd do next

- Capture groups and backreferences (needs a different match strategy than
  plain NFA acceptance).
- `{m,n}` bounded repeats.
- Anchors (`^`, `$`, `\b`) and a real multiline mode.
- DFA minimization (Hopcroft) — subset construction already helps, but the
  state tables are not minimal.
