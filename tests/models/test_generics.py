from MEDFORD.models.generics import KeywordMDL
from MEDFORD import MFD
import pytest 


def test_Keyword_model(tmpdir) :
    test_str = "@Keyword key"

    tmp_file = tmpdir / "test.mfd"
    tmp_file.write(test_str)

    res = MFD._get_unvalidated_blocks(tmp_file)
    d = MFD._get_dictionizer({}, {})
    dict = d.generate_dict(res)['Keyword'][0]
    a = KeywordMDL(**dict)
    assert 1
    print(a)