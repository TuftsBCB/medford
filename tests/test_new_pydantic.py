from typing import List, Tuple, Dict
from MEDFORD.objs.linecollections import Block, Line
from MEDFORD.objs.linecollector import LineCollector as LC
from MEDFORD.objs.linereader import LineReader as LR
from MEDFORD.objs.dictionizer import Dictionizer as D

from MEDFORD.models.generics import Contributor

class TestPydanticModels() :
    def setup_method(self, test_method) :
        pass

    def preprocess_lines(self, lines: List[str]) -> Tuple[List[Block], Dict[str, List[Dict]]] :
        line_objs: List[Line] = []
        for idx, l in enumerate(lines) :
            # TODO : shouldn't have to manually be getting rid of None lines tbh
            pl = LR.process_line(l, idx)
            if pl is not None :
                line_objs.append(pl)

        lc = LC(line_objs)
        bl = lc.named_blocks
        bls = [v for k,v in bl.items()]
        d = D(lc.defined_macros)
        return (bls, d.generate_dict(bls))

    def test_contributor(self) :
        sample_lines = [
            "@Contributor Polina Shpilker"
            ]
        
        (bls,cd) = self.preprocess_lines(sample_lines)
        contributor_data = cd['Contributor'][0]

        res = Contributor(**contributor_data)

        assert res.name[1] == "Polina Shpilker"
        assert res.name[0] == bls[0].headDetail
        assert res.Block == bls[0]