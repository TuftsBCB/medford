from MEDFORD.objs.dictionizer import Dictionizer
from MEDFORD.objs.linecollections import Block, Detail
from MEDFORD.objs.linereader import LineReader as LR
from MEDFORD.objs.linecollector import LineCollector as LC
from MEDFORD.objs.lines import Line

from typing import List, Dict, Any

class TestDictionizer() :
    def setup_method(self, test_method) :
        pass

    def preprocess_lines(self, lines: List[str]) -> List[Block]:
        line_objs: List[Line] = []
        for idx, l in enumerate(lines) :
            # TODO : shouldn't have to manually be getting rid of None lines tbh
            pl = LR.process_line(l, idx)
            if pl is not None :
                line_objs.append(pl)

        lc = LC(line_objs)
        bl = lc.get_flat_blocks()
        return bl

    #########################################
    # No Minor Tokens                       #
    #########################################

    def test_single_layer_dictionary_one_entry(self) :
        sample_lines = ["@Major name1"]
        bl = self.preprocess_lines(sample_lines)

        d = Dictionizer({},{})
        res_d : Dict[str, List[Dict]] = d.generate_dict(bl)
        assert len(res_d.keys()) == 1
        assert "Major" in res_d.keys()
        assert len(res_d["Major"]) == 1
        
        c_d: Dict[str, Any] = res_d["Major"][0]
        assert len(c_d.keys()) == 2
        assert c_d["Block"] == bl[0]
        assert c_d["name"][1] == "name1"
    
    def test_single_layer_dictionary_two_same_entry(self) :
        sample_lines = ["@Major name1", "@Major name2"]
        bl = self.preprocess_lines(sample_lines)

        d = Dictionizer({}, {})
        res_d : Dict[str, List[Dict]] = d.generate_dict(bl)
        assert len(res_d.keys()) == 1
        assert "Major" in res_d.keys()
        assert len(res_d["Major"]) == 2
        
        c_d: Dict[str, Any] = res_d["Major"][0]
        assert len(c_d.keys()) == 2
        assert c_d["Block"] == bl[0]
        assert c_d["name"][1] == "name1"

        c_d: Dict[str, Any] = res_d["Major"][1]
        assert len(c_d.keys()) == 2
        assert c_d["Block"] == bl[1]
        assert c_d["name"][1] == "name2"

    def test_single_layer_dictionary_two_diff_entry(self) :
        # TODO : number in major token throws unuseful error; make useful
        sample_lines = ["@Major name1", "@MajorTwo name2"]
        bl = self.preprocess_lines(sample_lines)

        d = Dictionizer({}, {})
        res_d : Dict[str, List[Dict]] = d.generate_dict(bl)
        assert len(res_d.keys()) == 2
        assert "Major" in res_d.keys()
        assert len(res_d["Major"]) == 1
        assert "MajorTwo" in res_d.keys()
        assert len(res_d["MajorTwo"]) == 1
        
        c_d: Dict[str, Any] = res_d["Major"][0]
        assert len(c_d.keys()) == 2
        assert c_d["Block"] == bl[0]
        assert c_d["name"][1] == "name1"

        c_d: Dict[str, Any] = res_d["MajorTwo"][0]
        assert len(c_d.keys()) == 2
        assert c_d["Block"] == bl[1]
        assert c_d["name"][1] == "name2"

    #########################################
    # Simple Minor Tokens                   #
    #########################################

    def test_double_layer_dictionary_one_entry(self) :
        sample_lines = [
            "@Major name1",
            "@Major-minor minor1"
            ]
        bl = self.preprocess_lines(sample_lines)

        d = Dictionizer({}, {})
        res_d : Dict[str, List[Dict]] = d.generate_dict(bl)
        assert len(res_d.keys()) == 1
        assert "Major" in res_d.keys()
        assert len(res_d["Major"]) == 1
        
        c_d: Dict[str, Any] = res_d["Major"][0]
        assert len(c_d.keys()) == 3
        assert c_d["Block"] == bl[0]
        assert c_d["name"][1] == "name1"
        assert 'minor' in c_d.keys()
        assert len(c_d["minor"][0]) == 2
        assert isinstance(c_d["minor"][0][0], Detail)
        assert c_d["minor"][0][1] == "minor1"