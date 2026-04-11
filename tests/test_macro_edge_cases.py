"""
macro syntax edge cases testing file
Author: Yaman Bosnali
Date: 04/05/2026

Scenarios tested here are:
1. Template with missing required params -> empty-string substitution (no crash)
2. Multiple templates in one file, full pipeline
3. Regression: plain files (no macros) still parse correctly after expand_templates
   was added to the pipeline
4. Macros combined with @include: macro scope stays in main file and included
   blocks appear without interference
5. Macro chaining: macro A references macro B, etc.
6. Circular/max-depth macros: A references B, B references A, etc.
7. Inline comment stripping: `@name Value # comment resolves to just Value
"""

import sys
sys.path.insert(0, "src")

import pytest
import MEDFORD.mfdglobals as mfdglobals
from MEDFORD import MFD
from MEDFORD.objs.template_utils import expand_templates


@pytest.fixture(autouse=True)
def reset_validator():
    mfdglobals.ForceNewValidator()



# Test 1 – Template with missing required params 
def test_template_missing_required_params_expands_to_empty():
    """Tests wheather params without defaults expand to empty string when 
    not provided at invocation.

    Documented behaviorr: no error is raised at template expansion time.
    the caller gets lines with empty substituted values.
    """
    lines = [
        "@>contrib_bare name dept\n",
        ">@contributor {name}\n",
        ">@contributor-department {dept}\n",
        "@<contrib_bare\n",
    ]
    expanded = expand_templates(lines)

    joined = "".join(expanded)
    assert "@>" not in joined, "@> definition should be removed"
    assert "@<" not in joined, "@< invocation should be removed"

    assert "@contributor \n" in expanded
    assert "@contributor-department \n" in expanded


def test_template_missing_required_params_full_pipeline():
    """Full pipeline on test_template_missing_param.mfd.

    Documented behavior: When a template parameter has no default and is 
    not provided at invocation, expand_templates substitutes an empty string.  
    The resulting line becomes '@contributor' (no trailing content), 
    which the LineReader cannot match.
    This currently raises NotImplementedError...documenting the known crash.
    """
    mfd = MFD("samples/test_template_missing_param.mfd", "compile", "validate")
    with pytest.raises(NotImplementedError):
        mfd.run_medford()


# Test 2 – Multiple templates, full pipeline
def test_multiple_templates_full_pipeline():
    """Test whether three templates with five invocations all expand 
    and validate correctly."""

    mfd = MFD("samples/test_multiple_templates.mfd", "compile", "validate")
    mfd.run_medford()

    assert not mfdglobals.validator.instance().has_syntax_err()

    blocks = mfd.line_collector.get_flat_blocks()
    resolved = {
        n: m.resolve(mfd.line_collector.defined_macros)
        for n, m in mfd.line_collector.defined_macros.items()
    }

    contributor_contents = [
        b.head_detail.get_content(resolved)
        for b in blocks
        if "contributor" in b.get_str_major().lower()
    ]

    # Five invocations must each produce a contributor block
    assert len(contributor_contents) == 5, (
        f"Expected 5 contributor blocks, got {len(contributor_contents)}: "
        f"{contributor_contents}"
    )

    all_text = " ".join(contributor_contents)
    assert "Bob Smith" in all_text
    assert "Alice Jones" in all_text
    assert "Alva Couch" in all_text   # template 1 invoked with defaults
    assert "Anonymous" in all_text    # template 3 default name
    assert "Carol Chen" in all_text   # template 3 override



# Test 3 – plain files without any macros
def test_expand_templates_is_noop_on_plain_lines():
    """Test if any regression happened by feeding in simple tags wiht no
    template syntax."""

    lines = [
        "@MEDFORD description\n",
        "@MEDFORD-Version 1.0\n",
        "@Contributor Alice\n",
        "@Contributor-Association Tufts\n",
    ]
    assert expand_templates(lines) == lines


def test_plain_file_full_pipeline_regression(tmp_path):
    """Test wheter a .mfd file with no macros still parses properly after 
    expand_templates was sent into _get_line_objects."""

    mfd_file = tmp_path / "plain.mfd"
    mfd_file.write_text(
        "@MEDFORD no macros here\n"
        "@MEDFORD-Version 1.0\n"
        "@Contributor Alice Smith\n"
        "@Contributor-Association Tufts University\n",
        encoding="utf-8",
    )

    mfd = MFD(str(mfd_file), "compile", "validate")
    mfd.run_medford()   # must not raise

    assert not mfdglobals.validator.instance().has_syntax_err()
    blocks = mfd.line_collector.get_flat_blocks()
    assert any("Contributor" in b.get_str_major() for b in blocks)


# Test 4 – Macros combined with @include: no cross-file interference
def test_macros_with_include_no_interference(tmp_path):
    """Tests whether a macro defined in the main file resolves correctly 
    while an @include statement brings in external blocks.  
    The two features must not interfere with each other."""

    included = tmp_path / "contrib.mfd"
    included.write_text(
        "@Contributor Bob\n"
        "@Contributor-Association MIT\n",
        encoding="utf-8",
    )

    main = tmp_path / "main.mfd"
    main.write_text(
        "@MEDFORD macro plus include test\n"
        "@MEDFORD-Version 1.0\n"
        "`@institution Tufts University\n"
        "@Contributor Alice\n"
        "@Contributor-Association `institution\n"
        f"@include contrib.mfd @Contributor\n",
        encoding="utf-8",
    )

    # Pass base_dir so IncludeCollector resolves includes relative to tmp_path
    mfd = MFD(str(main), "compile", "validate", base_dir=str(tmp_path))
    mfd.run_medford()

    assert not mfdglobals.validator.instance().has_syntax_err()

    resolved = {
        n: m.resolve(mfd.line_collector.defined_macros)
        for n, m in mfd.line_collector.defined_macros.items()
    }
    assert resolved["institution"] == "Tufts University"

    blocks = mfd.line_collector.get_flat_blocks()
    contributor_names = [
        b.head_detail.get_content(resolved)
        for b in blocks
        if "contributor" in b.get_str_major().lower()
    ]
    assert "Alice" in contributor_names, f"Alice missing from {contributor_names}"
    assert "Bob" in contributor_names, f"Bob missing from {contributor_names}"



# Test 5 – Macro chaining
def test_macro_chaining():
    """Tests what happens when a macro references another macro, which may reference another, etc."""

    from MEDFORD.objs.linereader import LineReader
    from MEDFORD.objs.linecollector import LineCollector

    lines = [
        "`@first Jane",
        "`@full `first Doe",
        "@Major `full",
    ]
    processed = [LineReader.process_line(s, i) for i, s in enumerate(lines)]
    processed = [p for p in processed if p is not None]
    lc = LineCollector(processed)

    resolved = {n: m.resolve(lc.defined_macros) for n, m in lc.defined_macros.items()}
    assert resolved["first"] == "Jane"
    assert resolved["full"] == "Jane Doe"

    blocks = lc.get_flat_blocks()
    assert blocks[0].head_detail.get_content(resolved) == "Jane Doe"


# Test 6 – Circular/max-depth macros
def test_circular_macro_hits_max_depth_gracefully():
    """Tests whether circular references (A to B to A) terminate at MAX_DEPTH 
    instead of looping.

    The resolver should stop at depth 10 and record a MaxMacroDepthExceeded error.
    """

    from MEDFORD.objs.linereader import LineReader
    from MEDFORD.objs.linecollector import LineCollector

    lines = [
        "`@a `b",
        "`@b `a",
    ]
    processed = [LineReader.process_line(s, i) for i, s in enumerate(lines)]
    processed = [p for p in processed if p is not None]
    lc = LineCollector(processed)

    result = lc.defined_macros["a"].resolve(lc.defined_macros)

    assert result == "ERROR", f"Expected 'ERROR' sentinel, got {result!r}"
    assert mfdglobals.validator.instance().has_other_err()


# Test 7 – Inline comment stripping
def test_inline_comment_stripped_end_to_end():
    """Tests whether inline # comments are stripped from macro values.

    Verifies the strip happens during macro definition (via parse_simple_macro_def)
    """
    from MEDFORD.objs.linereader import LineReader
    from MEDFORD.objs.linecollector import LineCollector

    lines = [
        "`@name Value # this is a comment",
        "@Major `name",
    ]
    processed = [LineReader.process_line(s, i) for i, s in enumerate(lines)]
    processed = [p for p in processed if p is not None]
    lc = LineCollector(processed)

    resolved = {n: m.resolve(lc.defined_macros) for n, m in lc.defined_macros.items()}
    assert resolved["name"] == "Value", (
        f"Expected 'Value', got {resolved['name']!r}, comment was not stripped"
    )

    blocks = lc.get_flat_blocks()
    content = blocks[0].head_detail.get_content(resolved)
    assert "comment" not in content
    assert content == "Value"
