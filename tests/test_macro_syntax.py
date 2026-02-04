"""Quick tests for new macro syntax (simple vars)."""
import re

# macro_use_regex
macro_use_regex = (
    r"`(?!@)(?:(?P<r1>\{(?P<mname_closed>[a-zA-Z0-9_]+)\})|"
    r"(?P<r2>(?P<mname_open>[a-zA-Z0-9_]+))(?=\s|$|\}))"
)


def test_macro_use_regex():
    cases = [
        ("`foo ", ["foo"]),
        ("`{bar}", ["bar"]),
        ("`@def x", []),
        ("a `b c", ["b"]),
        ("`x`y", ["y"]),  # `x not matched: no \\s|$|} after
    ]
    for s, expected in cases:
        ms = list(re.finditer(macro_use_regex, s))
        names = [m.group("mname_closed") or m.group("mname_open") for m in ms]
        assert names == expected, f"{s!r} -> {names} != {expected}"


def test_macro_utils():
    from MEDFORD.objs.macro_utils import parse_simple_macro_def, parse_braced_value

    assert parse_simple_macro_def("`@name value") == ("name", "value")
    assert parse_simple_macro_def("`@name {a value}") == ("name", "a value")
    assert parse_simple_macro_def("`@name {chaos {reigns}}") == ("name", "chaos {reigns}")
    assert parse_braced_value("{chaos {reigns}}") == ("chaos {reigns}", 16)


def test_braced_value_e2e():
    """Braced value `@name {chaos {reigns}}; use `name expands to chaos {reigns}."""
    from MEDFORD.objs.linereader import LineReader
    from MEDFORD.objs.linecollector import LineCollector

    lines = [
        "`@chaos chaos {reigns}",
        "@Major says `chaos",
    ]
    processed = [LineReader.process_line(s, i) for i, s in enumerate(lines)]
    processed = [p for p in processed if p is not None]
    lc = LineCollector(processed)
    m = lc.defined_macros["chaos"]
    assert m.resolve(lc.defined_macros) == "chaos {reigns}"
    blocks = lc.get_flat_blocks()
    assert len(blocks) == 1
    resolved = {n: mac.resolve(lc.defined_macros) for n, mac in lc.defined_macros.items()}
    assert blocks[0].head_detail.get_content(resolved) == "says chaos {reigns}"


if __name__ == "__main__":
    test_macro_use_regex()
    test_macro_utils()
    test_braced_value_e2e()
    print("ok")
