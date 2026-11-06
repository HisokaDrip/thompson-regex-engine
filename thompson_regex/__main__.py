"""CLI: python -m thompson_regex 'pattern' [file|-]"""

from __future__ import annotations

import argparse
import sys

from .matcher import compile
from .parser import RegexSyntaxError


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="thompson_regex",
        description="Match a regex (Thompson NFA) against a file or stdin.",
    )
    p.add_argument("pattern", help="regex pattern")
    p.add_argument(
        "path",
        nargs="?",
        default="-",
        help="file to search (default: stdin)",
    )
    p.add_argument(
        "--dfa",
        action="store_true",
        help="compile NFA→DFA for matching",
    )
    p.add_argument(
        "--fullmatch",
        action="store_true",
        help="require the whole line to match",
    )
    args = p.parse_args(argv)

    try:
        rx = compile(args.pattern, use_dfa=args.dfa)
    except RegexSyntaxError as e:
        print(f"pattern error: {e}", file=sys.stderr)
        return 2

    if args.path == "-":
        lines = sys.stdin.read().splitlines(keepends=False)
    else:
        with open(args.path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines(keepends=False)

    found = 0
    for i, line in enumerate(lines, 1):
        if args.fullmatch:
            m = rx.match(line)
            hits = [m.group()] if m else []
        else:
            hits = rx.findall(line)
        for h in hits:
            print(f"{i}:{h}")
            found += 1
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
