"""Multi-line template macros: @>name params, >@ body, @<name invocation.
Params without defaults use empty string when not provided at invocation."""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TemplateDef:
    name: str
    params: Dict[str, Optional[str]]  # param -> default (None = no default)
    body_lines: List[str]


def _strip_comment(s: str) -> str:
    idx = s.find("#")
    return s[:idx].rstrip() if idx >= 0 else s


def _parse_params(rest: str) -> Dict[str, Optional[str]]:
    """Parse name dept or name={val} dept={val} into param -> default."""
    from .macro_utils import parse_braced_value

    rest = _strip_comment(rest).strip()
    out: Dict[str, Optional[str]] = {}
    i = 0
    while i < len(rest):
        while i < len(rest) and rest[i].isspace():
            i += 1
        if i >= len(rest):
            break
        start = i
        while i < len(rest) and (rest[i].isalnum() or rest[i] == "_"):
            i += 1
        pname = rest[start:i]
        while i < len(rest) and rest[i].isspace():
            i += 1
        if i < len(rest) and rest[i] == "=" and i + 1 < len(rest) and rest[i + 1] == "{":
            val, n = parse_braced_value(rest[i + 1 :])
            out[pname] = val
            i += 1 + n
        else:
            out[pname] = None
    return out


def _substitute(text: str, values: Dict[str, str]) -> str:
    """Replace {varname} with values. Simple: {word} only (word = alphanumeric + _)."""
    def repl(m):
        return values.get(m.group(1), "")
    return re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, text)


def expand_templates(raw_lines: List[str]) -> List[str]:
    """Extract template defs, expand @< invocations. Returns processed lines."""
    templates: Dict[str, TemplateDef] = {}
    output: List[str] = []
    i = 0

    while i < len(raw_lines):
        line = raw_lines[i]
        s = line.strip()

        if not s:
            output.append(line)
            i += 1
            continue

        # Template def: @>name p1 p2 or @>name p1={v1}
        if re.match(r"@>[A-Za-z]", s):
            s = _strip_comment(s).strip()
            name = re.match(r"@>([A-Za-z0-9_]+)", s).group(1)
            rest = s[2 + len(name) :].lstrip()
            params = _parse_params(rest)
            body = []
            i += 1
            while i < len(raw_lines) and raw_lines[i].strip().startswith(">"):
                body.append(raw_lines[i])
                i += 1
            templates[name] = TemplateDef(name, params, body)
            continue

        # Template invocation: @<name or @<name p1={v1}
        if re.match(r"@<[A-Za-z]", s):
            s = _strip_comment(s).strip()
            name = re.match(r"@<([A-Za-z0-9_]+)", s).group(1)
            rest = s[2 + len(name) :].lstrip()
            args_raw = _parse_params(rest) if rest else {}
            args = {k: v for k, v in args_raw.items() if v is not None}
            if name in templates:
                t = templates[name]
                values = {}
                for p, d in t.params.items():
                    values[p] = args.get(p, d if d is not None else "")
                for bline in t.body_lines:
                    stripped = bline.strip().lstrip(">").strip()
                    output.append(_substitute(stripped, values) + "\n")
            else:
                output.append(line)
            i += 1
            continue

        # Orphan body line (skip)
        if s.startswith(">"):
            i += 1
            continue

        output.append(line)
        i += 1

    return output
