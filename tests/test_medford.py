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

def test_get_line_objects_one() :
    from MEDFORD.objs.lines import NovelDetailLine
    test_line = ["@Major content"]
    test_idx = range(0,len(test_line))
    test_list = zip(test_line, test_idx)

    res_obj_list = MFD._get_line_objects(test_list)
    
    assert isinstance(res_obj_list[0], NovelDetailLine)

def test_get_line_objects_mult() :
    from MEDFORD.objs.lines import NovelDetailLine, ContinueLine
    test_line = ["@Major content","@Major-minor content","continue"]
    test_idx = range(0,len(test_line))
    test_list = zip(test_line, test_idx)

    res_obj_list = MFD._get_line_objects(test_list)
    
    assert isinstance(res_obj_list[0], NovelDetailLine)
    assert isinstance(res_obj_list[1], NovelDetailLine)
    assert isinstance(res_obj_list[2], ContinueLine)

def test_get_line_objects_none() :
    # TODO: should there be a warning or something when this happens?
    test_line = []
    test_idx = []
    test_list = zip(test_line, test_idx)

    res_obj_list = MFD._get_line_objects(test_list)

    assert len(res_obj_list) == 0

def test_get_line_objs_from_file_one(tmp_path) :
    from MEDFORD.objs.lines import NovelDetailLine
    tmp_file_content = "@Major content"

    d = tmp_path / "test_line_objs"
    d.mkdir()

    f = d / "test_one.mfd"
    f.write_text(tmp_file_content)

    res_obj_list = MFD._get_line_objs_from_file(f)
    assert isinstance(res_obj_list[0], NovelDetailLine)

def test_get_line_objs_from_file_mult(tmp_path) :
    from MEDFORD.objs.lines import NovelDetailLine, ContinueLine
    tmp_file_content = "@Major content\n@Major-minor content\ncontinue"

    d = tmp_path / "test_line_objs"
    d.mkdir()

    f = d / "test_mult.mfd"
    f.write_text(tmp_file_content)

    res_obj_list = MFD._get_line_objs_from_file(f)
    assert isinstance(res_obj_list[0], NovelDetailLine)
    assert isinstance(res_obj_list[1], NovelDetailLine)
    assert isinstance(res_obj_list[2], ContinueLine)

def test_get_line_objs_from_file_empty(tmp_path) :
    d = tmp_path / "test_line_objs"
    d.mkdir()

    f = d / "test_empty.mfd"
    f.write_text("")

    res_obj_list = MFD._get_line_objs_from_file(f)
    assert len(res_obj_list) == 0