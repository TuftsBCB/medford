from MEDFORD.submodules.medforderrors.errors import *

import MEDFORD.mfdglobals as mfdglobals
from MEDFORD.objs.linecollections import Detail, Macro
from MEDFORD.objs.linereader import LineReader as LR
from MEDFORD.objs.linecollector import LineCollector as LC, Line, NovelDetailLine
from MEDFORD.objs.dictionizer import Dictionizer

from typing import List, Dict

class ProcessToLineObj() :
    def preprocess_lines(self, lines: List[str]) -> List[Line] :
        line_objs: List[Line] = []
        for idx, l in enumerate(lines) :
            # TODO : shouldn't have to manually be getting rid of None lines tbh
            pl = LR.process_line(l, idx)
            if pl is not None :
                line_objs.append(pl)

        return line_objs

class ProcessToMacros() :
    def preprocess_lines(self, lines: List[str]) -> Dict[str,Macro] :
        line_objs: List[Line] = []
        for idx, l in enumerate(lines) :
            # TODO : shouldn't have to manually be getting rid of None lines tbh
            pl = LR.process_line(l, idx)
            if pl is not None :
                line_objs.append(pl)

        lc = LC(line_objs)
        ma = lc.defined_macros
        return ma

class TestMissingDescErr(ProcessToLineObj) :
    def setup_method(self, test_method) :
        pass

    def test_help_message(self) :
        line_objs = self.preprocess_lines([
            "@Major-minor content"
        ])[0]

        assert isinstance(line_objs, NovelDetailLine)
        test_detail: Detail = Detail(line_objs)
        err: MissingDescError = MissingDescError(test_detail)

        assert err.msg == "A new block for major token Major was created at line 0 without a Name line."
        assert err.helpmsg == "A MEDFORD Block should begin with a line like this:\n@Major (name of this medford block)\n@Major-minor content"
        assert err.errtype == ErrType.SYNTAX
        assert err.errname == "MissingDescError"

class TestMaxMacroDepthErr(ProcessToMacros) :
    def test_help_message(self) :
        line_objs: Dict[str, Macro] = self.preprocess_lines([
            "`@Macro1 content ",
            "content continue",
            "`@Macro2 `@Macro1",
            "`@Macro3 `@Macro2",
            "`@Macro4 `@Macro3",
            "`@Macro5 `@Macro4",
            "`@Macro6 `@Macro5",
            "`@Macro7 `@Macro6",
            "`@Macro8 `@Macro7",
            "`@Macro9 `@Macro8",
            "`@Macro0 `@Macro9",
        ])

        corrected_order: List[Macro] = [line_objs[name] for name in [
            'Macro0', 
            'Macro9', 
            'Macro8',
            'Macro7', 
            'Macro6', 
            'Macro5',
            'Macro4', 
            'Macro3', 
            'Macro2',
            'Macro1', 
            ]]
        
        err: MaxMacroDepthExceeded = MaxMacroDepthExceeded(corrected_order)
        assert err.msg == "Macro Macro0 on line 10 is 11 references deep in a macro reference chain. (Macro history: Macro0->Macro9->Macro8->Macro7->Macro6->Macro5->Macro4->Macro3->Macro2->Macro1)"
        assert err.helpmsg == "You can use a macro within a macro only up to 10 macros deep. You may have an loop of references (e.g. macro 1 uses macro 2, but macro 2 uses macro 1), or you need to reduce the number of layers. The full text of your macro reference is below: \nLines (10-10): (Macro0) `@Macro9\nLines (9-9): (Macro9) `@Macro8\nLines (8-8): (Macro8) `@Macro7\nLines (7-7): (Macro7) `@Macro6\nLines (6-6): (Macro6) `@Macro5\nLines (5-5): (Macro5) `@Macro4\nLines (4-4): (Macro4) `@Macro3\nLines (3-3): (Macro3) `@Macro2\nLines (2-2): (Macro2) `@Macro1\nLines (0-1): (Macro1) content content continue\n"
        # TODO : hanging \n, do we do anything about it?
        assert err.errtype == ErrType.OTHER
        assert err.errname == "MaxMacroDepthExceeded"

    # fun fact: on first implementation, if lines was not reversed,
    #   it would work fine.
    # e.g. :    "M1 a"      vs      "M3 M2"
    #           "M2 M1"             "M2 M1"
    #           "M3 M2"             "M1 a"
    # in the first one, it is resolved in order of M1, M2, M3.
    #   thus, M1: nothing to check, resolved.
    #           M2: checks M1, it is resolved, goes only 1 deep. resolved.
    #           M3: checks M2, it is resolved, goes only 1 deep. resolved.
    #   vs, M3: checks M2, not resolved, recurses:
    #       -> M2: checks M1, not resolved, rescurses:
    #       ->  -> M1: nothing to check, resolved. went 2 deep.
    # in response, adjusted Macro to annotate the number of resolutions
    #   it took, so we don't have inconsistent behavior based on resolution
    #   order.
    def test_natural_creation(self) :

        lines = [
            "`@Macro1 content ",
            "content continue",
            "`@Macro2 `@Macro1",
            "`@Macro3 `@Macro2",
            "`@Macro4 `@Macro3",
            "`@Macro5 `@Macro4",
            "`@Macro6 `@Macro5",
            "`@Macro7 `@Macro6",
            "`@Macro8 `@Macro7",
            "`@Macro9 `@Macro8",
            "`@Macro10 `@Macro9",
            "`@Macro11 `@Macro10",
        ]
        lines.reverse()
        line_objs: Dict[str, Macro] = self.preprocess_lines(lines)

        valr = mfdglobals.validator
        print(valr._id)
        d = Dictionizer(line_objs, {})
        error_coll = valr._other_err_coll
        assert len(error_coll.keys()) == 1
        assert 0 in error_coll.keys()
        errs: List[MFDErr] = error_coll[0]
        assert len(errs) == 1
        assert isinstance(errs[0], MaxMacroDepthExceeded)
        err: MaxMacroDepthExceeded = errs[0]
        assert err.errtype == "MaxMacroDepthExceeded"
        assert err.macros[0].name == "Macro11"
        assert err.macros[0].get_raw_content() == "`@Macro10"

    # Ensuring that max macro depth is upheld no matter resolution
    #   order.
    def test_natural_creation_not_reversed(self) :
        lines = [
            "`@Macro1 content ",
            "content continue",
            "`@Macro2 `@Macro1",
            "`@Macro3 `@Macro2",
            "`@Macro4 `@Macro3",
            "`@Macro5 `@Macro4",
            "`@Macro6 `@Macro5",
            "`@Macro7 `@Macro6",
            "`@Macro8 `@Macro7",
            "`@Macro9 `@Macro8",
            "`@Macro10 `@Macro9",
            "`@Macro11 `@Macro10",
        ]
        line_objs: Dict[str, Macro] = self.preprocess_lines(lines)
        
        valr = mfdglobals.validator
        valr._clear_errors()
        d = Dictionizer(line_objs, {})
        error_coll = valr._other_err_coll
        assert len(error_coll.keys()) == 1
        assert 11 in error_coll.keys()
        errs: List[MFDErr] = error_coll[11]
        assert len(errs) == 1
        assert isinstance(errs[0], MaxMacroDepthExceeded)
        err: MaxMacroDepthExceeded = errs[0]
        assert err.errtype == "MaxMacroDepthExceeded"
        assert err.macros[0].name == "Macro11"
        assert err.macros[0].get_raw_content() == "`@Macro10"





