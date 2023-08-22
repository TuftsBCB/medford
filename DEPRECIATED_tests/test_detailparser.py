import pytest

from MEDFORD.medford_detail import *
from MEDFORD.medford_detailparser import *

@pytest.fixture
def general_context() :
    emngr = error_mngr("ALL","LINE")
    detail._clear_cache()
    return [emngr]

def test_single_line(general_context) :
    emngr = general_context[0]

    line = "@Date 02/24"
    
    d = detail.FromLine(line, -1, None, emngr)
    p = detailparser([d.detail], emngr)
    out_dict = p.export()
    
    assert list(out_dict.keys()) == ["Date"]
    assert len(out_dict["Date"]) == 1

    assert list(out_dict["Date"][0][1].keys()) == ["desc"]
    assert len(out_dict["Date"][0][1]["desc"]) == 1

    assert out_dict["Date"][0][1]["desc"][0][1] == "02/24"

    assert len(emngr.return_syntax_errors()) == 0

def test_multiple_details_one_instance(general_context):
    emngr = general_context[0]

    line = "@Date 02/24"
    line2 = "@Date-note Hello World"

    ds = []
    dr = detail.FromLine(line, -1, None, emngr)
    ds.append(dr.detail)
    ds.append(detail.FromLine(line2, -1, dr, emngr).detail)
    p = detailparser(ds, emngr)
    out_dict = p.export()

    assert list(out_dict.keys()) == ["Date"]
    assert len(out_dict["Date"]) == 1

    assert list(out_dict["Date"][0][1].keys()) == ["desc","note"]
    assert len(out_dict["Date"][0][1]["desc"]) == 1
    assert len(out_dict["Date"][0][1]["note"]) == 1

    assert out_dict["Date"][0][1]["desc"][0][1] == "02/24"
    assert out_dict["Date"][0][1]["note"][0][1] == "Hello World"

    assert len(emngr.return_syntax_errors()) == 0

def test_multiple_notes_one_instance(general_context):
    emngr = general_context[0]
    line1 = "@Date 02/24"
    line2 = "@Date-note Hello World"
    line3 = "@Date-note 42"

    ds = []
    dr = detail.FromLine(line1, -1, None, emngr)
    ds.append(dr.detail)
    dr = detail.FromLine(line2, -1, dr, emngr)
    ds.append(dr.detail)
    dr = detail.FromLine(line3, -1, dr, emngr)
    ds.append(dr.detail)

    p = detailparser(ds, emngr)
    out_dict = p.export()

    assert list(out_dict["Date"][0][1].keys()) == ["desc","note"]
    assert len(out_dict["Date"][0][1]["note"]) == 2

    assert out_dict["Date"][0][1]["desc"][0][1] == "02/24"
    assert out_dict["Date"][0][1]["note"][0][1] == "Hello World"
    assert out_dict["Date"][0][1]["note"][1][1] == "42"

    assert len(emngr.return_syntax_errors()) == 0
