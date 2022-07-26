import pytest

from MEDFORD.medford_detail import *

@pytest.fixture()
def general_context() :
    err_mngr = error_mngr("ALL", "LINE")
    detail._clear_cache()
    return [err_mngr]

def test_detail_simple(general_context) :
    err_mngr = general_context[0]
    example_line = "@Date 02/24"
    dr = detail.FromLine(example_line, -1, None, err_mngr)
    d = dr.detail
    assert d.Major_Tokens == ["Date"]
    assert d.Minor_Token == "desc"
    assert d.Data == "02/24"

def test_detail_ordinary(general_context) :
    err_mngr = general_context[0]

    # Have to work around the 'detailreturn' type requirement. Otherwise, runs into
    #     an error where it tries to check data in None. This is correct error catching
    #     behavior, but it's not what we want for this test.
    example_line = "@Date 02/24"
    dr = detail.FromLine(example_line, -1, None, err_mngr)
    example_line = "@Date-Note Samples Obtained"
    dr = detail.FromLine(example_line, -1, dr, err_mngr)
    d = dr.detail
    assert d.Major_Tokens == ["Date"]
    assert d.Minor_Token == "Note"
    assert d.Data == "Samples Obtained"

def test_detail_2_level_recursive(general_context) :
    err_mngr = general_context[0]

    example_line = "@Freeform_Date asdf"
    dr = detail.FromLine(example_line, -1, None, err_mngr)
    example_line = "@Freeform_Date-Note Samples Obtained"
    dr = detail.FromLine(example_line, -1, dr, err_mngr)
    d = dr.detail
    assert d.Major_Tokens == ["Freeform","Date"]
    assert d.Minor_Token == "Note"
    assert d.Data, "Samples Obtained"

def test_recognizes_template(general_context) :
    err_mngr = general_context[0]
    example_line = "@Date [..]"

    detail.FromLine(example_line, -1, None, err_mngr)

    errors = err_mngr.return_syntax_errors()
    assert len(errors) == 1
    assert errors[-1][0].errtype == "remaining_template"

def test_detail_multiline(general_context) :
    err_mngr = general_context[0]

    example_line_0 = "@Date 02-22-2022"
    example_line_1 = "@Date-Note asdf "
    example_line_2 = "More asdf"

    dr = detail.FromLine(example_line_0, -1, None, err_mngr)
    dr = detail.FromLine(example_line_1, -1, dr, err_mngr)
    dr = detail.FromLine(example_line_2, -1, dr, err_mngr)
    assert dr.detail.Data == "asdf More asdf"

# Tests for Macro functionality.
def test_add_macro(general_context) :
    err_mngr = general_context[0]

    example_line = "`@macro_name macro body"

    dr = detail.FromLine(example_line, -1, None, err_mngr)

    assert list(detail.macro_dictionary.keys()) == ["macro_name"]

def test_add_multiple_macros(general_context) :
    err_mngr = general_context[0]

    example_line = "`@macro_name macro body"
    example_line_2 = "`@macro_name_2 macro body"
    
    dr = detail.FromLine(example_line, -1, None, err_mngr)
    dr = detail.FromLine(example_line_2, -1, dr, err_mngr)

    assert list(detail.macro_dictionary.keys()) == ["macro_name", "macro_name_2"]

def test_add_same_macro_name(general_context) :
    err_mngr = general_context[0]

    example_line = "`@macro_name macro body"
    example_line_2 = "`@macro_name macro body"
    
    dr = detail.FromLine(example_line, -1, None, err_mngr)
    dr = detail.FromLine(example_line_2, -1, dr, err_mngr)

    errors = err_mngr.return_syntax_errors()
    assert len(errors) == 1
    assert errors[-1][0].errtype == "duplicated_macro"

def test_correctly_substitutes_macro(general_context) :
    err_mngr = general_context[0]

    example_line = "`@macro_name macro body"
    example_line_2 = "@major-minor text `@macro_name"

    dr = detail.FromLine(example_line, -1, None, err_mngr)
    dr = detail.FromLine(example_line_2, -1, dr, err_mngr)

    assert dr.detail.Data == "text macro body"

def test_correctly_substitutes_macro_with_stuff_after(general_context) :
    err_mngr = general_context[0]

    example_line = "`@macro_name macro body"
    example_line_2 = "@major-minor text `@macro_name asdf asdf asdf"

    dr = detail.FromLine(example_line, -1, None, err_mngr)
    dr = detail.FromLine(example_line_2, -1, dr, err_mngr)

    assert dr.detail.Data == "text macro body asdf asdf asdf"

def test_correctly_substitutes_macro_curled(general_context) :
    err_mngr = general_context[0]

    example_line = "`@macro_name macro body"
    example_line_2 = "@major-minor text `@{macro_name} asdf asdf"

    dr = detail.FromLine(example_line, -1, None, err_mngr)
    dr = detail.FromLine(example_line_2, -1, dr, err_mngr)

    assert dr.detail.Data == "text macro body asdf asdf"

def test_accepts_multiline_macro(general_context) :
    err_mngr = general_context[0]

    example_line = "`@macro_name macro_body"
    example_line_2 = "macro_body_2"
    
    dr = detail.FromLine(example_line, -1, None, err_mngr)
    dr = detail.FromLine(example_line_2, -1, dr, err_mngr)
    
    assert list(detail.macro_dictionary.keys()) == ["macro_name"]
    assert detail.macro_dictionary[dr.macro[0]] == (-1, "macro_body macro_body_2")

    assert len(err_mngr.return_syntax_errors()) == 0

def test_substitutes_multiline_macro(general_context) :
    err_mngr = general_context[0]

    macro_body_1 = "macro_body"
    macro_body_2 = "macro_body_2"
    
    example_line = "`@macro_name " + macro_body_1
    example_line_2 = macro_body_2
    example_line_3 = "@major `@macro_name"

    dr = detail.FromLine(example_line, -1, None, err_mngr)
    dr = detail.FromLine(example_line_2, -1, dr, err_mngr)
    dr = detail.FromLine(example_line_3, -1, dr, err_mngr)

    assert dr.detail.Data == macro_body_1 + " " + macro_body_2
    
    assert len(err_mngr.return_syntax_errors()) == 0

# Tests for Comment functionality
def test_ignores_inline_in_macro(general_context) :
    err_mngr = general_context[0]

    example_line = "`@macro_name macro_body # this is a comment"

    dr = detail.FromLine(example_line, -1, None, err_mngr)

    assert detail.macro_dictionary[dr.macro[0]] == (-1, "macro_body")


def test_removes_whitespaces_before_comment(general_context) :
    err_mngr = general_context[0]
    example_line = "@Major body # comment"

    dr = detail.FromLine(example_line, -1, None, err_mngr)
    assert dr.detail.Data == "body"