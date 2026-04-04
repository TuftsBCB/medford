"""Tests for simple variable macro syntax."""
import re

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
        ("`x`y", ["y"]),
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


def test_macro_utils_inline_comment():
    """Inline comment is stripped from unbraced macro value."""
    from MEDFORD.objs.macro_utils import parse_simple_macro_def

    assert parse_simple_macro_def("`@name value # trailing comment") == ("name", "value")
    assert parse_simple_macro_def("`@foo bar baz # comment") == ("foo", "bar baz")


def test_macro_utils_unbraced_with_spaces():
    """Unbraced value captures rest of line (including spaces) up to #."""
    from MEDFORD.objs.macro_utils import parse_simple_macro_def

    assert parse_simple_macro_def("`@x a b c") == ("x", "a b c")
    assert parse_simple_macro_def("`@name Tufts University") == ("name", "Tufts University")


def test_macro_utils_braced_empty():
    """Empty braced value parses correctly."""
    from MEDFORD.objs.macro_utils import parse_braced_value, parse_simple_macro_def

    assert parse_braced_value("{}") == ("", 2)
    assert parse_simple_macro_def("`@empty {}") == ("empty", "")


def test_macro_utils_invalid_inputs():
    """Invalid inputs raise ValueError."""
    from MEDFORD.objs.macro_utils import parse_simple_macro_def, parse_braced_value
    import pytest

    with pytest.raises(ValueError, match="must start with"):
        parse_simple_macro_def("@name value")
    with pytest.raises(ValueError, match="Missing macro value"):
        parse_simple_macro_def("`@name")
    with pytest.raises(ValueError, match="expects string starting with"):
        parse_braced_value("x{}")
    with pytest.raises(ValueError, match="Unmatched braces"):
        parse_braced_value("{unclosed")


def test_macro_chain_resolution():
    """Macros can reference other macros; resolution follows chain."""
    from MEDFORD.objs.linereader import LineReader
    from MEDFORD.objs.linecollector import LineCollector

    lines = [
        "`@base Tufts",
        "`@mid `base University",
        "`@full `mid - Engineering",
        "@Major institution: `full",
    ]
    processed = [LineReader.process_line(s, i) for i, s in enumerate(lines)]
    processed = [p for p in processed if p is not None]
    lc = LineCollector(processed)
    resolved = {n: m.resolve(lc.defined_macros) for n, m in lc.defined_macros.items()}
    assert resolved["base"] == "Tufts"
    assert resolved["mid"] == "Tufts University"
    assert resolved["full"] == "Tufts University - Engineering"
    blocks = lc.get_flat_blocks()
    assert blocks[0].head_detail.get_content(resolved) == "institution: Tufts University - Engineering"


def test_macro_use_braced_and_unbraced():
    """Both `name and `{name} forms expand correctly."""
    from MEDFORD.objs.linereader import LineReader
    from MEDFORD.objs.linecollector import LineCollector

    lines = [
        "`@a alpha",
        "`@b beta",
        "@Major `a and `{b}",
    ]
    processed = [LineReader.process_line(s, i) for i, s in enumerate(lines)]
    processed = [p for p in processed if p is not None]
    lc = LineCollector(processed)
    resolved = {n: m.resolve(lc.defined_macros) for n, m in lc.defined_macros.items()}
    blocks = lc.get_flat_blocks()
    assert blocks[0].head_detail.get_content(resolved) == "alpha and beta"


def test_simple_macro_full_pipeline():
    """Full MFD pipeline: test_macros.mfd parses and validates."""
    import MEDFORD.mfdglobals as mfdglobals
    mfdglobals.ForceNewValidator()

    from MEDFORD import MFD
    mfd = MFD("samples/test_macros.mfd", "compile", "validate")
    mfd.run_medford()
    assert not mfdglobals.validator.instance().has_syntax_err()
    blocks = mfd.line_collector.get_flat_blocks()
    resolved = {n: m.resolve(mfd.line_collector.defined_macros) for n, m in mfd.line_collector.defined_macros.items()}
    contrib_block = [b for b in blocks if "Contributor" in b.get_str_major()][0]
    content = contrib_block.head_detail.get_content(resolved)
    assert "Alva L. Couch" in content
    assert resolved["author_name"] == "Alva L. Couch"
    assert resolved["institution"] == "Tufts University"
    assert resolved["chaos"] == "chaos {reigns}"


if __name__ == "__main__":
    test_macro_use_regex()
    test_macro_utils()
    test_braced_value_e2e()
    test_macro_utils_inline_comment()
    test_macro_utils_unbraced_with_spaces()
    test_macro_utils_braced_empty()
    test_macro_utils_invalid_inputs()
    test_macro_chain_resolution()
    test_macro_use_braced_and_unbraced()
    test_simple_macro_full_pipeline()
    print("ok")
