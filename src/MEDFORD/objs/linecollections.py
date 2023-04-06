from typing import Optional, List, Dict
from MEDFORD.objs.lines import Line, ContinueLine, ContentMixin, MacroLine, NovelDetailLine

# create mixin for macro, named obj handling
class LineCollection() :
    headline: ContentMixin
    extralines: Optional[List[ContinueLine]]

    has_macros: bool = False
    used_macro_names: Optional[List[str]]

    def __init__(self, headline: ContentMixin, extralines: Optional[List[ContinueLine]]) :
        self.headline = headline
        self.extralines = extralines

        if headline.has_macros :
            self.has_macros = True
            self.used_macro_names = [m[2] for m in headline.macro_uses]
        
        if extralines is not None :
            for el in extralines :
                if el.has_macros :
                    self.has_macros = True
                    if self.used_macro_names is None :
                        self.used_macro_names = []
                    self.used_macro_names = [m[2] for m in el.macro_uses]

    # don't implement yet, will do after rework is done.
    #has_references: bool = False
    #references: Optional[list[str]]

    def _validate_depth(self, macro_definitions: Dict[str, 'Macro'], depth: int) :
        if self.has_macros and self.used_macro_names is not None :
            if depth >= 9 :
                raise ValueError("Maximum macro recursion of 10 reached.")
            for macro_name in self.used_macro_names :
                macro_definitions[macro_name]._validate_depth(macro_definitions, depth + 1)


    def substitute_macros(self, macro_definitions: Dict[str, 'Macro'], depth: Optional[int]) -> None :
        raise NotImplementedError()

class Macro(LineCollection) :
    name : str

    def __init__(self, headline: MacroLine, extralines: Optional[List[ContinueLine]]):
        super(Macro, self).__init__(headline, extralines)
        self.name = headline.macro_name

    def get_raw_content(self) -> str :
        outstr = self.headline.raw_content
        if self.extralines is not None :
            for el in self.extralines :
                outstr = outstr + el.raw_content
        return outstr

    def get_content(self, macro_definitions: Dict[str, 'Macro']) -> str :
        if self.has_macros and self.used_macro_names is not None :
            # tell the macros to solve themselves
            solved_macros: Dict[str, str] = dict()
            for macro_name in self.used_macro_names :
                solved_macros[macro_name] = macro_definitions[macro_name].get_content(macro_definitions)
            
            self.headline.replace_macros(solved_macros)
            if self.extralines is not None :
                for exline in self.extralines :
                    exline.replace_macros(solved_macros)
        raise NotImplementedError()
    
class Detail(LineCollection) :
    major_token: str
    minor_token: Optional[str]
    is_header: bool
    # payload should only be obtained at the end, so macros, etc can be accurately replaced

#    _fulldesc: List[Union[NovelDetailLine, ContinueLine]] # keep LineReturns so we can extract comments, linenos later

    
    def __init__(self, headline: NovelDetailLine, extralines: Optional[List[ContinueLine]] = None) :
        '''
        Create a Detail object from one DETAIL type LineReturn and any number of CONT type LineReturns.

        Parameters
        ------
        lines: List[Line]
        '''
        
        self.headline = headline
        self.extralines = extralines

        # find major, minor tokens from first line
        self.major_token = headline.major_token
        self.minor_token = headline.minor_token

        if self.minor_token is None :
            self.is_header = True

        self.validate()

    def validate(self) :
        raise NotImplementedError()
        return

    def get_raw_content(self) -> str :
        out = self.headline.raw_content
        if self.extralines is not None :
            for l in self.extralines :
                # TODO : deal with spacing
                out = out + l.raw_content
        return out
    
    def get_content(self, macro_dict: Dict[str, str]) -> str :
        raise NotImplementedError("")
        return ""

class Block(LineCollection) :
    major_token: str
    minor_tokens: List[str]
    
    name: str

    def __init__(self, details: List[Detail]) :
        if len(details) == 0 :
            raise ValueError("Attempted to create a block with no details.")
        
        # ?
        self.major_token = details[0].major_token
        if details[0].minor_token is not None and details[0].minor_token != "" :
            raise ValueError("No desc line for first detail provided to Block constructor.")
        self.name = details[0].get_raw_content()

        if len(details) > 0 :
            for idx, detail in enumerate(details[1:]) :
                if detail.major_token != self.major_token :
                    raise ValueError("Block provided details of multiple major tokens: Block Major is %s while line %d has major of %s." % (self.major_token, idx, detail.major_token))
                if detail.minor_token is None :
                    raise ValueError("Block provided a detail with no minor token past first detail: detail # %d." % (idx))
                
                self.minor_tokens.append(detail.minor_token)

                if detail.has_macros and detail.used_macro_names is not None :
                    if self.used_macros is None :
                        self.used_macros = []
                        self.has_macros = True

                    for macro_use in detail.used_macro_names :
                        if macro_use not in self.used_macros :
                            self.used_macros.append(macro_use)

        return

