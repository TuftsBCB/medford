import pytest
from typing import List, Optional, Dict
from MEDFORD.objs.lines import Line, MacroLine
from MEDFORD.objs.linereader import LineReader
from MEDFORD.objs.linecollector import LineCollector
from MEDFORD.objs.linecollections import Macro

class TestMacroCreation():
    def setup_method(self, test_method) :
        self.macro_strs: List[str] = [
            "`@Macro1 definition",
            "`@Macro2 `@Macro1",
            "`@Macro3 `@{Macro1}",
            "`@Macro4 `@Macro2",
            "`@Macro5 `@Macro2 asdf",
            "`@Macro6 `@Macro1 `@Macro2 asdf"
        ]

        self.macro_lines: List[Line] = []
        for idx, l in enumerate(self.macro_strs) :
            r = LineReader.process_line(l, idx)
            assert r is not None
            assert isinstance(r, MacroLine)

            self.macro_lines.append(r)

    def test_basic_macro(self) :
        cur_line: Line = self.macro_lines[0]
        lp: LineCollector = LineCollector([cur_line])
        lp_dm: Dict[str, Macro] = lp.defined_macros

        assert len(lp_dm.keys()) == 1
        assert lp_dm["Macro1"] is not None
        mobj = lp_dm["Macro1"]
        assert mobj.has_macros == False
        assert mobj.get_raw_content() == "definition"
        # TODO : test get_content once that's implemented
