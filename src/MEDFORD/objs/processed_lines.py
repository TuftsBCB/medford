from typing import Optional, List, Dict
from MEDFORD.objs.lines import Line, ContinueLine, ContentMixin, MacroLine

# create mixin for macro, named obj handling
class ProcessedLine() :
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

class Macro(ProcessedLine) :
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