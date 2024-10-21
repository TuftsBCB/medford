from MEDFORD.medford import MFD
from MEDFORD.models.generics import Entity
import pytest 

@pytest.mark.skip(reason="Need to add a mode that doesn't throw errors on missing values. This does not have the required fields MEDFORD or Contributor, but should pass.")
def test_Keyword_model() :
    test_str = [("@Keyword key",0)]

    res = MFD._get_unvalidated_blocks(test_str)
    d = MFD._get_dictionizer({}, {})
    dict = d.generate_dict(res)
    a = Entity(**dict)
    assert 1
    print(a)