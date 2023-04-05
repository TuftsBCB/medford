from typing import List, Tuple, Optional, Union, Dict
from MEDFORD.objs.lines import NovelDetailLine, ContinueLine, Line
import re

class Detail :
    major_tokens: List[str]
    minor_token: Optional[str]
    # payload should only be obtained at the end, so macros, etc can be accurately replaced

    has_macros: bool = False
    macro_uses: Optional[List[str]]

    _fulldesc: List[Union[NovelDetailLine, ContinueLine]] # keep LineReturns so we can extract comments, linenos later

    
    def __init__(self, lines : List[Union[NovelDetailLine, ContinueLine]]) :
        '''
        Create a Detail object from one DETAIL type LineReturn and any number of CONT type LineReturns.

        Parameters
        ------
        lines: List[Line]
        '''
        if len(lines) == 0 :
            raise ValueError("At least one LineReturn must be provided to create a Detail object.")
        if len(lines) > 1 :
            for idx, l in enumerate(lines[1:]) :
                if not isinstance(l, ContinueLine) :
                    raise ValueError("Detail was provided a list of Line returns where the %d th object was not a ContinueLine." % idx)
        
        detail_line : Line = lines[0]
        if not isinstance(detail_line, NovelDetailLine) :
            raise ValueError("First provided Line must be a NovelDetailLine.")
        
        self._fulldesc = lines

        # find major, minor tokens from first line
        self.major_tokens = detail_line.major_tokens
        self.minor_token = detail_line.minor_token

        self.validate()
        self.gather_macros()

    def validate(self) :
        return

    def gather_macros(self) :
        found_macros = []
        for line in self._fulldesc :
            if line.has_macros :
                self.has_macros = True
                found_macros.append([macro[2] for macro in line.macro_uses])

    def raw_payload(self) -> str :
        out = ""
        for l in self._fulldesc :
            # TODO : deal with spacing
            out = out + l.payload
        return out
    
    def substituted_payload(self, macro_dict: Dict[str, str]) -> str :
        raise NotImplementedError("substituted_payload not yet implemented.")
        return ""
