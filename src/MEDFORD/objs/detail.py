from typing import List, Tuple, Optional, Union, Dict
from MEDFORD.objs.lines import NovelDetailLine, ContinueLine, Line
import re

class Detail :
    major_token: str
    minor_token: Optional[str]
    is_header: bool
    # payload should only be obtained at the end, so macros, etc can be accurately replaced

    has_macros: bool = False
    macro_uses: Optional[List[str]]

    _headline: NovelDetailLine
    _extralines: Optional[List[ContinueLine]]
#    _fulldesc: List[Union[NovelDetailLine, ContinueLine]] # keep LineReturns so we can extract comments, linenos later

    
    def __init__(self, headline: NovelDetailLine, extralines: Optional[List[ContinueLine]] = None) :
        '''
        Create a Detail object from one DETAIL type LineReturn and any number of CONT type LineReturns.

        Parameters
        ------
        lines: List[Line]
        '''
        
        self._headline = headline
        self._extralines = extralines

        # find major, minor tokens from first line
        self.major_token = headline.major_token
        self.minor_token = headline.minor_token

        if self.minor_token is None :
            self.is_header = True

        self.validate()
        self.gather_macros()

    def validate(self) :
        return

    def gather_macros(self) :
        found_macros = []
        if self._headline.has_macros :
            self.has_macros = True
            found_macros.append([macro[2] for macro in self._headline.macro_uses])

        if self._extralines is not None :
            for line in self._extralines :
                if line.has_macros :
                    self.has_macros = True
                    found_macros.append([macro[2] for macro in line.macro_uses])
        
        self.macro_uses = found_macros

    def raw_payload(self) -> str :
        out = self._headline.payload
        if self._extralines is not None :
            for l in self._extralines :
                # TODO : deal with spacing
                out = out + l.payload
        return out
    
    def substituted_payload(self, macro_dict: Dict[str, str]) -> str :
        raise NotImplementedError("substituted_payload not yet implemented.")
        return ""
