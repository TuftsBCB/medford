import pytest
from MEDFORD.objs.lines import CommentLine,MacroLine,NovelDetailLine,ContinueLine
from MEDFORD.objs.linereader import LineReader

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
    ]
    return {"examples": example_lines, "invalid": invalid_lines}

#################################
# Tests                         #
#################################

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

# TODO : move tests over from test_linereader to test "find" capabilities