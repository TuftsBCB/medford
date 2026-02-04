"""Helpers for simple variable macro syntax.

Defining a variable:
  `@name Value
  – or –
  `@name {A value}   # if spaces in value

Braced values: brace matching.  `@name {chaos {reigns}}  →  `name  expands to  chaos {reigns}

Expanding:  `name  or  `{name}   # optional braces (no @ in use)
"""

from typing import Tuple, Optional


def parse_braced_value(s: str) -> Tuple[str, int]:
    """Parse a brace-delimited value with matching braces.

    s must start with '{'. Returns (value, end_index) where value is the
    content up to the matching '}', and end_index is the index past the
    closing '}'. Inner braces are preserved in the value.

    Example: '{chaos {reigns}}' -> ('chaos {reigns}', 17)
    """
    if not s or s[0] != "{":
        raise ValueError("parse_braced_value expects string starting with {")
    depth = 0
    i = 0
    start = 1
    while i < len(s):
        if s[i] == "{":
            depth += 1
            if depth == 1:
                start = i + 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return (s[start:i].strip(), i + 1)
        i += 1
    raise ValueError("Unmatched braces in braced value")


def parse_simple_macro_def(line: str) -> Tuple[str, str]:
    """Parse a simple macro definition line.

    Supports:
      `@name Value
      `@name {A value with spaces}

    Returns (name, value). Strips leading/trailing whitespace from line first.
    """
    line = line.strip()
    if not line.startswith("`@"):
        raise ValueError("Simple macro definition must start with `@")
    rest = line[2:].lstrip()
    if not rest:
        raise ValueError("Missing macro name and value after `@")
    # name: [A-Za-z0-9_]+
    i = 0
    while i < len(rest) and (rest[i].isalnum() or rest[i] == "_"):
        i += 1
    if i == 0:
        raise ValueError("Macro name must start with letter")
    name = rest[:i]
    rest = rest[i:].lstrip()
    if not rest:
        raise ValueError("Missing macro value")
    if rest.startswith("{"):
        value, _ = parse_braced_value(rest)
        return (name, value)
    # Unbraced: rest of line; strip inline # comment
    idx = rest.find("#")
    if idx >= 0:
        rest = rest[:idx].rstrip()
    return (name, rest)
