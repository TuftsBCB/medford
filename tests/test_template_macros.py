"""Tests for multi-line template macros: @>, >@, @<."""

import sys
sys.path.insert(0, "src")

from MEDFORD.objs.template_utils import expand_templates, TemplateDef


def test_template_expansion():
    lines = [
        "@MEDFORD description\n",
        "@>contrib_tufts name={Alva} dept={Eng}\n",
        ">@contributor {name}\n",
        ">@contributor-department {dept}\n",
        "@<contrib_tufts\n",
    ]
    expanded = expand_templates(lines)
    assert "@contributor Alva\n" in expanded
    assert "@contributor-department Eng\n" in expanded
    assert "@>" not in "".join(expanded)
    assert "@<" not in "".join(expanded)


def test_template_params_without_defaults():
    """Params without defaults use empty string when not provided."""
    lines = [
        "@>greet name title\n",
        ">Hello {title} {name}\n",
        "@<greet name={Alice} title={Dr}\n",
    ]
    expanded = expand_templates(lines)
    assert "Hello Dr Alice\n" in expanded


def test_template_params_with_defaults_override():
    """Explicit args override defaults at invocation."""
    lines = [
        "@>foo x={default}\n",
        ">x is {x}\n",
        "@<foo x={override}\n",
    ]
    expanded = expand_templates(lines)
    assert "x is override\n" in expanded


def test_template_multiple_invocations():
    """Same template can be invoked multiple times with different args."""
    lines = [
        "@>contrib name dept\n",
        ">@contributor {name}\n",
        ">@contributor-department {dept}\n",
        "@<contrib name={Alice} dept={CS}\n",
        "@<contrib name={Bob} dept={Math}\n",
    ]
    expanded = expand_templates(lines)
    assert "@contributor Alice\n" in expanded
    assert "@contributor-department CS\n" in expanded
    assert "@contributor Bob\n" in expanded
    assert "@contributor-department Math\n" in expanded


def test_template_empty_body():
    """Template with no body lines produces no output lines on invocation."""
    lines = [
        "@>empty x\n",
        "@<empty x={a}\n",
    ]
    expanded = expand_templates(lines)
    assert len(expanded) == 0


def test_template_orphan_body_skipped():
    """Orphan > lines (not part of template) are skipped."""
    lines = [
        ">@orphan line\n",
        "@MEDFORD description\n",
    ]
    expanded = expand_templates(lines)
    assert expanded == ["@MEDFORD description\n"]


def test_template_undefined_invocation_passthrough():
    """Invoking undefined template leaves line unchanged."""
    lines = [
        "@<nonexistent\n",
    ]
    expanded = expand_templates(lines)
    assert expanded == ["@<nonexistent\n"]


def test_template_inline_comment_in_def():
    """Inline comment in template def header is stripped."""
    lines = [
        "@>foo x={a} # comment\n",
        ">{x}\n",
        "@<foo\n",
    ]
    expanded = expand_templates(lines)
    assert "a\n" in expanded


def test_template_expansion_full_pipeline():
    """Run MEDFORD on template file and verify it validates."""
    import MEDFORD.mfdglobals as mfdglobals
    mfdglobals.ForceNewValidator()

    from MEDFORD import MFD
    mfd = MFD("samples/test_template_macro.mfd", "compile", "validate")
    mfd.run_medford()
    assert not mfdglobals.validator.instance().has_syntax_err()
