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


def test_template_expansion_full_pipeline():
    """Run MEDFORD on template file and verify it validates."""
    import MEDFORD.mfdglobals as mfdglobals
    mfdglobals.ForceNewValidator()

    from MEDFORD import MFD
    mfd = MFD("samples/test_template_macro.mfd", "compile", "validate")
    mfd.run_medford()
    assert not mfdglobals.validator.instance().has_syntax_err()
