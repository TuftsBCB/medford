from random import choice
from MEDFORD.medford import OutputMode
from MEDFORD.medford import MFD

def test_OutputModeEnum() :
    test_lowercase = ['OTHER', 'BCODMO', 'RDF', 'BAGIT']
    test_uppercase = [x.upper() for x in test_lowercase]
    test_wild = [''.join(choice((str.upper, str.lower))(char) for char in test_str) for test_str in test_lowercase]
    
    test_lowercase.extend(test_uppercase)
    test_lowercase.extend(test_wild)

    for test_str in test_lowercase :
        assert OutputMode(test_str) is not None

# sanity check to make sure devs check that all versions were properly incremented.
def test_get_version() :
    assert MFD.get_version() == "2.0.0"