import pytest

from pathlib import PurePath
from MEDFORD.medford import *

def test_pdam_cunning() :
    runMedford(PurePath("samples/pdam_cunning.MFD"), True, MFDMode.OTHER, ErrorMode.all, ErrorOrder.line, ParserMode.validate)
    assert True

def test_freeform() :
    runMedford(PurePath("samples/made_up_Freeform.MFD"), True, MFDMode.OTHER, ErrorMode.all, ErrorOrder.line, ParserMode.validate)
    assert True

def test_bcodmo() :
    runMedford(PurePath("samples/made_up_BCODMO.MFD"), True, MFDMode.BCODMO, ErrorMode.all, ErrorOrder.line, ParserMode.validate)
    assert True

def test_bagit() :
    runMedford(PurePath("samples/bagit_example/made_up_BAGIT.MFD"), True, MFDMode.BAGIT, ErrorMode.all, ErrorOrder.line, ParserMode.validate)
    assert True

# TODO: Test to make sure that comments are NOT causing unexpected behavior
# 07/04/22 bug behavior - 
# @Date 05/09
# # comment 1
# # comment 2
# @Date-Note date received
#
# Was causing the following dictionary structure:
# {Date : [
#   (12,{'desc': [...]}),
#   (12,{'desc': [...]}),
#   (12,{'desc': [...], 'Note': [...]})
# ]}
# ALSO TODO: @MEDFORD-Version is case-sensitive... this shouldn't be the case.
# ALSO TODO: Something is going horribly wrong with the pydantic error translation... Work on re-working it?
def test_comments_not_duplicating(tmp_path) :
    sample_txt = "@MEDFORD testing_comments\n@MEDFORD-Version 1.0\n\n@Date 05/09\n# comment 1\n#comment 2\n #comment 3\n@Date-Note asdf"

    f = tmp_path / "sample.mfd"
    f.write_text(sample_txt)

    runMedford(tmp_path / "sample.mfd", True, MFDMode.OTHER, ErrorMode.all, ErrorOrder.line, ParserMode.validate)

    with open(tmp_path / "sample.mfd.JSON", 'r') as jf:
        res_json = json.load(jf)
        assert 'Date' in res_json.keys()
        assert len(res_json['Date']) == 1
        assert 'desc' in res_json['Date'][0][1]
        assert 'Note' in res_json['Date'][0][1]
        assert len(res_json['Date'][0][1]['desc']) == 1
        assert len(res_json['Date'][0][1]['Note']) == 1

# The MEDFORD parser has checks for missing 'desc' lines. However, these checks fail if the very first line
#   is a missing desc line. Check to make sure that this fix hasn't been broken.
def test_no_crash_on_first_line_missing_desc(tmp_path) :
    sample_txt = ["",
                "@MEDFORD-Version 1.0"]

    f = tmp_path / "sample.mfd"
    f.write_text("\n".join(sample_txt))

    try :
        runMedford(tmp_path / "sample.mfd", True, MFDMode.OTHER, ErrorMode.all, ErrorOrder.line, ParserMode.validate)
    except SystemExit as e:
        assert True # system exit is fine, means we caught it appropriately
    except Exception as e:
        assert 0 # any other exception is bad

# Ensure that a comment-only line is appropriately seen as an empty line by pydantic and caught as an error by the medford parser.
def test_comment_only_is_considered_empty(tmp_path) :

    err_mngr = error_mngr("ALL", "LINE")
    detail._clear_cache()

    sample_txt = ["@MEDFORD testing",
                    "@MEDFORD-Version # I think the verison is 1.0?"]
    
    f = tmp_path / "sample.mfd"
    f.write_text("\n".join(sample_txt))

    try :
        details = read_details(f, err_mngr)
    except SystemExit as e:
        assert True
    except Exception as e:
        assert 0