from MEDFORD.objs.linecollector import LineCollector
from MEDFORD.objs.linereader import LineReader
from MEDFORD.objs.lines import *
from MEDFORD.objs.linecollections import Macro

from typing import Optional


class TestLineCollection() :
    def setup_method(self, test_method) :
        pass


    def test_process_only_comment(self) :
        test_line: Optional[Line] = LineReader.process_line("#Comment", 0)
        assert test_line is not None

        confirmed_line : Line = test_line

        # TODO : do I like that you HAVE to create a LineCollector object?
        #           can't just call ProcessLines on its own?
        lc : LineCollector = LineCollector([confirmed_line])
        assert len(lc.named_blocks.keys()) == 0
        assert len(lc.defined_macros.keys()) == 0
        assert len(lc.comments) == 1
        assert lc.comments[0] == confirmed_line

    def test_process_only_macro(self) :
        test_line: Optional[Line] = LineReader.process_line("`@Macro value", 0)
        assert test_line is not None
        assert isinstance(test_line, MacroLine)

        confirmed_line : MacroLine = test_line

        lc : LineCollector = LineCollector([confirmed_line])
        assert len(lc.named_blocks.keys()) == 0
        assert len(lc.defined_macros.keys()) == 1
        assert len(lc.comments) == 0
        # TODO : expose this functionality in LineCollector so it can be called instead
        #           of reconstructed manually?
        assert lc.defined_macros[confirmed_line.macro_name] == Macro(confirmed_line, None)
        


