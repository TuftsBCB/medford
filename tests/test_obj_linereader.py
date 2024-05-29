import pytest
from MEDFORD.objs.lines import AtAtLine, CommentLine,MacroLine,NovelDetailLine,ContinueLine
from MEDFORD.objs.linereader import LineReader
from submodules.mfdvalidator.validator import MedfordValidator as em
from MEDFORD.submodules.mfdvalidator.errors import MissingAtAtName

#################################
# Fixtures                      #
#################################

@pytest.fixture(scope="session")
def comment_ex_fixture() :
    example_lines = [
        "#Comment Line",
        "# Comment Line"
    ]
    invalid_lines = [
        "Not a # Comment Line"
    ]
    return {"examples": example_lines, "invalid": invalid_lines}

@pytest.fixture(scope="session")
def macro_ex_fixture() :
    example_lines = [
        "`@Name value",
        "`@Name value 1 value 2"
        "`@Name value1 # inline"
        "`@Name `@use"
    ]
    invalid_lines = [
        "`@ Not a macro",
        "'@Not a macro",
        "'@ Not a macro",
    ]
    return {"examples": example_lines, "invalid": invalid_lines}

@pytest.fixture(scope="session")
def noveldetail_ex_fixture() :
    example_lines = [
        "@Major data",
        "@Major data data",
        "@Major-minor data",
        "@Major_Major-minor data",
    ]
    invalid_lines = [
        "@ Major data",
        #"@Major-minor-minor data", 
        # ^^ Technically not invalid, should be a Detail error not a line parsing error
    ]
    return {"examples": example_lines, "invalid": invalid_lines}

#################################
# Tests                         #
#################################

class TestAtAtImplementation() :
    def test_detect_atat(self) :
        example_line = "@Major-@MajorTwo Content"
        assert isinstance(LineReader.process_line(example_line, 0), AtAtLine)
    
    def test_err_on_unnamed_atat(self) :
        example_line = "@Major-@MajorTwo"
        with pytest.raises(Exception) :
            LineReader.process_line(example_line, 0)
        assert len(em.instance()._syntax_err_coll) == 1
        assert isinstance(em.instance()._syntax_err_coll[0][0], MissingAtAtName)

    def test_detect_atat_with_comment(self) :
        example_line = "@Major-@MajorTwo Content # Inline"
        res = LineReader.process_line(example_line, 0)
        assert isinstance(res, AtAtLine)
        assert res.has_inline
        assert res.get_content({}) == "Content"
    
    def test_detect_atat_with_macro(self) :
        example_line = "@Major-@MajorTwo Content `@Macro"
        res = LineReader.process_line(example_line, 0)
        assert isinstance(res, AtAtLine)
        assert res.has_macros
        assert len(res.macro_uses) == 1
        assert res.macro_uses[0][2] == "Macro"
        assert res.get_content({'Macro':'value'}) == "Content value"

    def test_detect_atat_with_latex(self) :
        example_line = "@Major-@MajorTwo Content $$Tex$$"
        res = LineReader.process_line(example_line, 0)
        assert isinstance(res, AtAtLine)
        assert res.has_tex
        assert len(res.tex_locs) == 1
        assert res.get_content({}) == "Content $$Tex$$"

def test_detect_comment(comment_ex_fixture, macro_ex_fixture, noveldetail_ex_fixture) :
    examples = comment_ex_fixture['examples']
    nonexamples = comment_ex_fixture['invalid']
    macros = macro_ex_fixture['examples']
    noveldetail = noveldetail_ex_fixture['examples']
    for ex in examples :
        assert isinstance(LineReader.process_line(ex, 0), CommentLine)
    for nex in nonexamples :
        assert not isinstance(LineReader.process_line(nex, 0), CommentLine)
    for m in macros :
        assert not isinstance(LineReader.process_line(m, 0), CommentLine)
    for nd in noveldetail :
        assert not isinstance(LineReader.process_line(nd, 0), CommentLine)

def test_detect_newmacro(macro_ex_fixture, comment_ex_fixture, noveldetail_ex_fixture) :
    examples = macro_ex_fixture['examples']
    nonexamples = macro_ex_fixture['invalid']
    comments = comment_ex_fixture['examples']
    noveldetail = noveldetail_ex_fixture['examples']
    for ex in examples :
        assert isinstance(LineReader.process_line(ex, 0), MacroLine)
    for nex in nonexamples :
        assert not isinstance(LineReader.process_line(nex, 0), MacroLine)
    for c in comments :
        assert not isinstance(LineReader.process_line(c, 0), MacroLine)
    for nd in noveldetail :
        assert not isinstance(LineReader.process_line(nd, 0), MacroLine)

def test_detect_noveldetail(noveldetail_ex_fixture, macro_ex_fixture, comment_ex_fixture) :
    examples = noveldetail_ex_fixture['examples']
    nonexamples = noveldetail_ex_fixture['invalid']
    comments = comment_ex_fixture['examples']
    macros = macro_ex_fixture['examples']
    for ex in examples :
        assert isinstance(LineReader.process_line(ex, 0), NovelDetailLine)
    for nex in nonexamples :
        assert not isinstance(LineReader.process_line(nex, 0), NovelDetailLine)
    for c in comments :
        assert not isinstance(LineReader.process_line(c, 0), NovelDetailLine)
    for m in macros:
        assert not isinstance(LineReader.process_line(m, 0), NovelDetailLine)

def test_detect_macro_badcurly() :
    # TODO : smart recognize this mis-use and throw an error?
    example_lines = [
        "@Major wrong{`@macrouse}"
    ]
    res = LineReader.process_line(example_lines[0], 0)
    assert res is not None
    assert isinstance(res, NovelDetailLine)
    assert res.has_macros
# TODO : move tests over from test_linereader to test "find" capabilities
# TODO : add test for major-minor identification
# TODO : add raw content setting tests (e.g. mname, mbody)

# TODO : add test to check indices of returned regex.
#           reason: regex returns *were* including space after the regex *sometimes*. That is unacceptable.