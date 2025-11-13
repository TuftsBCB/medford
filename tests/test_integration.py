from MEDFORD import provide_args_and_go, ParserMode, OutputMode
from MEDFORD.mfdglobals import ForceNewValidator
import pytest

# example error case:
# no Contributor tag -> crash

@pytest.fixture(autouse=True)
def force_new_validator():
    ForceNewValidator()

# error 1 : leading tabs are not deleted.
# error 2 : removing contributor causes it to crash.
def test_no_contributor(tmpdir) :
    example_content = "@MEDFORD asdf\n\
@MEDFORD-Version 2.0\n\
\n\
@Journal journal\n\
"
    
    tmpfile = tmpdir / "quicktest.mfd"
    tmpfile.write_text(example_content, encoding="utf-8")
    print(example_content)

    provide_args_and_go(ParserMode.VALIDATE, tmpfile, OutputMode.OTHER)
    return

def test_lead_spacing_not_ignored(tmp_path) :
    example_content = "\
        @MEDFORD asdf\n\
        @MEDFORD-Version 2.0\n\
        \n\
        @Journal journal\n\
        "
    
    d = tmp_path / "tmp_testfiles"
    d.mkdir()
    tmpfile = d / "only_MEDFORD.mfd"
    tmpfile.write_text(example_content, encoding="utf-8")

    with pytest.raises(ValueError) :
        provide_args_and_go(ParserMode.VALIDATE, tmpfile, OutputMode.OTHER)
    return


# error 1 : leading tabs are not deleted.
# error 2 : removing contributor causes it to crash.
def test_no_contributor(tmp_path):
    example_content = "\
@MEDFORD asdf\n\
@MEDFORD-Version 2.0\n\
\n\
@Journal journal\n\
"

    d = tmp_path / "tmp_testfiles"
    d.mkdir()
    tmpfile = d / "only_MEDFORD.mfd"
    tmpfile.write_text(example_content, encoding="utf-8")

    provide_args_and_go(ParserMode.VALIDATE, tmpfile, OutputMode.OTHER)
    return


def test_lead_spacing_not_ignored(tmp_path):
    example_content = "\
        @MEDFORD asdf\n\
        @MEDFORD-Version 2.0\n\
        \n\
        @Journal journal\n\
        "

    d = tmp_path / "tmp_testfiles"
    d.mkdir()
    tmpfile = d / "only_MEDFORD.mfd"
    tmpfile.write_text(example_content, encoding="utf-8")

    with pytest.raises(ValueError):
        provide_args_and_go(ParserMode.VALIDATE, tmpfile, OutputMode.OTHER)
    return
