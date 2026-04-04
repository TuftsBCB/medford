from typing import Dict, List
import pytest
from MEDFORD.submodules.mfdvalidator.errors import *

import MEDFORD.mfdglobals as mfdglobals
from MEDFORD.objs.dictionizer import Dictionizer
from MEDFORD.objs.linecollections import Detail, Macro
from MEDFORD.objs.linecollector import Line, NovelDetailLine
from MEDFORD.objs.linecollector import LineCollector as LC
from MEDFORD.objs.linereader import LineReader as LR
from MEDFORD.submodules.mfdvalidator.errors import (
    ErrType,
    MaxMacroDepthExceeded,
    MFDErr,
    MissingDescError,
)


@pytest.fixture(autouse=True)
def force_new_validator():
    mfdglobals.ForceNewValidator()

class ProcessToLineObj() :
    def preprocess_lines(self, lines: List[str]) -> List[Line] :
        line_objs: List[Line] = []
        for idx, l in enumerate(lines):
            # TODO :shouldn't have to manually be getting rid of None lines tbh
            pl = LR.process_line(l, idx)
            if pl is not None:
                line_objs.append(pl)

        return line_objs


class ProcessToMacros:
    def preprocess_lines(self, lines: List[str]) -> Dict[str, Macro]:
        line_objs: List[Line] = []
        for idx, l in enumerate(lines):
            # TODO :shouldn't have to manually be getting rid of None lines tbh
            pl = LR.process_line(l, idx)
            if pl is not None:
                line_objs.append(pl)

        lc = LC(line_objs)
        ma = lc.defined_macros
        return ma


class TestMissingDescErr(ProcessToLineObj):
    def setup_method(self, test_method):
        pass

    def test_help_message(self):
        line_objs = self.preprocess_lines(["@Major-minor content"])[0]

        assert isinstance(line_objs, NovelDetailLine)
        test_detail: Detail = Detail(line_objs)
        err: MissingDescError = MissingDescError(test_detail)

        assert (
            err.msg
            == "A new block for major token Major was created at line 0 without a Name line."
        )
        assert (
            err.helpmsg
            == "A MEDFORD Block should begin with a line like this:\n@Major (name of this medford block)\n@Major-minor content"
        )
        assert err.errtype == ErrType.SYNTAX
        assert err.errname == "MissingDescError"


class TestMaxMacroDepthErr(ProcessToMacros):
    def test_help_message(self):
        # Use `name not `@name; simple macros single-line.
        line_objs: Dict[str, Macro] = self.preprocess_lines(
            [
                "`@Macro1 content",
                "`@Macro2 `Macro1",
                "`@Macro3 `Macro2",
                "`@Macro4 `Macro3",
                "`@Macro5 `Macro4",
                "`@Macro6 `Macro5",
                "`@Macro7 `Macro6",
                "`@Macro8 `Macro7",
                "`@Macro9 `Macro8",
                "`@Macro0 `Macro9",
            ]
        )

        corrected_order: List[Macro] = [
            line_objs[name]
            for name in [
                "Macro0",
                "Macro9",
                "Macro8",
                "Macro7",
                "Macro6",
                "Macro5",
                "Macro4",
                "Macro3",
                "Macro2",
                "Macro1",
            ]
        ]

        err: MaxMacroDepthExceeded = MaxMacroDepthExceeded(corrected_order)
        assert err.msg == (
            "Macro Macro0 on line 9 is 11 references deep in a "
            "macro reference chain. (Macro history: Macro0->Macro9"
            "->Macro8->Macro7->Macro6->Macro5->Macro4->Macro3->"
            "Macro2->Macro1)"
        )
        expected_help = (
            "You can use a macro within a macro only up to 10 macros deep. You may have an loop of references (e.g. macro 1 uses macro 2, but macro 2 uses macro 1), or you need to reduce the number of layers. The full text of your macro reference is below: \n"
            "Lines (9-9): (Macro0) `Macro9\n"
            "Lines (8-8): (Macro9) `Macro8\n"
            "Lines (7-7): (Macro8) `Macro7\n"
            "Lines (6-6): (Macro7) `Macro6\n"
            "Lines (5-5): (Macro6) `Macro5\n"
            "Lines (4-4): (Macro5) `Macro4\n"
            "Lines (3-3): (Macro4) `Macro3\n"
            "Lines (2-2): (Macro3) `Macro2\n"
            "Lines (1-1): (Macro2) `Macro1\n"
            "Lines (0-0): (Macro1) content\n"
        )
        assert err.helpmsg == expected_help
        assert err.errtype == ErrType.OTHER
        assert err.errname == "MaxMacroDepthExceeded"

    def test_natural_creation(self):
        lines = [
            "`@Macro1 content",
            "`@Macro2 `Macro1",
            "`@Macro3 `Macro2",
            "`@Macro4 `Macro3",
            "`@Macro5 `Macro4",
            "`@Macro6 `Macro5",
            "`@Macro7 `Macro6",
            "`@Macro8 `Macro7",
            "`@Macro9 `Macro8",
            "`@Macro10 `Macro9",
            "`@Macro11 `Macro10",
        ]
        lines.reverse()
        line_objs: Dict[str, Macro] = self.preprocess_lines(lines)

        valr = mfdglobals.validator
        d = Dictionizer(line_objs, {})
        error_coll = valr._other_err_coll
        assert len(error_coll) == 1
        errs: List[MFDErr] = next(iter(error_coll.values()))
        assert len(errs) == 1
        assert isinstance(errs[0], MaxMacroDepthExceeded)
        err: MaxMacroDepthExceeded = errs[0]
        assert err.errtype == ErrType.OTHER
        assert err.errname == "MaxMacroDepthExceeded"
        assert len(err.macros) >= 1
        assert any(m.name == "Macro11" for m in err.macros) or any(
            m.name == "Macro1" for m in err.macros
        )

    # Ensuring that max macro depth is upheld no matter resolution order.
    def test_natural_creation_not_reversed(self):
        lines = [
            "`@Macro1 content",
            "`@Macro2 `Macro1",
            "`@Macro3 `Macro2",
            "`@Macro4 `Macro3",
            "`@Macro5 `Macro4",
            "`@Macro6 `Macro5",
            "`@Macro7 `Macro6",
            "`@Macro8 `Macro7",
            "`@Macro9 `Macro8",
            "`@Macro10 `Macro9",
            "`@Macro11 `Macro10",
        ]
        line_objs: Dict[str, Macro] = self.preprocess_lines(lines)

        valr = mfdglobals.validator
        valr._clear_errors()
        d = Dictionizer(line_objs, {})
        error_coll = valr._other_err_coll
        assert len(error_coll.keys()) == 1
        errs: List[MFDErr] = list(error_coll.values())[0]
        assert len(errs) == 1
        assert isinstance(errs[0], MaxMacroDepthExceeded)
        err: MaxMacroDepthExceeded = errs[0]
        assert err.errtype == ErrType.OTHER
        assert err.errname == "MaxMacroDepthExceeded"
        assert err.macros[0].name == "Macro11"
        assert err.macros[0].get_raw_content() == "`Macro10"
