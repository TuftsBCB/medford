from typing import Optional, List, Dict, Tuple
from MEDFORD.objs.lines import Line, ContinueLine, ContentMixin, MacroLine, NovelDetailLine

# create mixin for macro, named obj handling
# TODO: separate LineCollection into a LineCollection and FeatureContainer
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
    
    def __eq__(self, other) -> bool :
        if type(self) != type(other) :
            return False

        if self.headline != other.headline :
            return False
        
        if self.has_macros != other.has_macros :
            return False
        elif self.has_macros and self.used_macro_names is not None:
            for idx, mn in self.used_macro_names :
                if mn != other.used_macro_names[idx] :
                    return False
        
        if (self.extralines is None) ^ (other.extralines is None) :
            return False
        else :
            if self.extralines is not None:
                if len(self.extralines) != len(other.extralines) :
                    return False
                else :
                    for idx, l in enumerate(self.extralines) :
                        if l != other.extralines[idx] :
                            return False

        
        return True


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
    
    def __eq__(self, other) -> bool :
        if type(self) == type(other) and self.name == other.name:
            return super(Macro, self).__eq__(other)
            
        return False


    
class Detail(LineCollection) :
    major_tokens: List[str]
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
        self.major_tokens = headline.major_tokens
        self.minor_token = headline.minor_token

        if self.minor_token is None :
            self.is_header = True
        else :
            self.is_header = False

        #self.validate()

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

    def __eq__(self, other) -> bool :
        if type(self) == type(other) :
            if self.major_tokens == other.major_tokens and self.is_header == other.is_header :
                if (self.minor_token is None) ^ (other.minor_token is None) :
                    return False
                elif self.minor_token != other.minor_token :
                    return False
                    
                return super(Detail, self).__eq__(other)
                
        return False

# TODO: this shouldn't be a LineCollection
class Block(LineCollection) :
    major_tokens: List[str]
    minor_tokens: Optional[List[Tuple[str, Detail]]] # Technically can have MFD block with nothing but a name
    details: List[Detail]
    
    name: str

    def __init__(self, details: List[Detail]) :
        if len(details) == 0 :
            raise ValueError("Attempted to create a block with no details.")
        
        self.details = details
        # ?
        self.major_tokens = details[0].major_tokens
        if details[0].minor_token is not None and details[0].minor_token != "" :
            raise ValueError("No desc line for first detail provided to Block constructor.")
        self.name = details[0].get_raw_content()

        if len(details) > 0 :
            self.minor_tokens = []
            for idx, detail in enumerate(details[1:]) :
                if detail.major_tokens != self.major_tokens :
                    raise ValueError("Block provided details of multiple major tokens: Block Major is %s while line %d has major of %s." % ("_".join(self.major_tokens), idx, "_".join(detail.major_tokens)))
                if detail.minor_token is None :
                    raise ValueError("Block provided a detail with no minor token past first detail: detail # %d." % (idx))
                
                self.minor_tokens.append((detail.minor_token, detail))

                if detail.has_macros and detail.used_macro_names is not None :
                    if self.used_macros is None :
                        self.used_macros = []
                        self.has_macros = True

                    for macro_use in detail.used_macro_names :
                        if macro_use not in self.used_macros :
                            self.used_macros.append(macro_use)

        return
    

    def __eq__(self, other) -> bool :
        if type(self) != type(other) :
            return False
        
        if self.major_tokens != other.major_tokens :
            return False
        
        if (self.minor_tokens is None) ^ (other.minor_tokens is None) :
            return False
        
        elif self.minor_tokens is not None :
            if len(self.minor_tokens) != len(other.minor_tokens) :
                return False
            else :
                for idx, t in enumerate(self.minor_tokens) :
                    if t != other.minor_tokens[idx] :
                        return False
        
        if len(self.details) != len(self.details) :
            return False
        else :
            for idx, d in enumerate(self.details) :
                if d != other.details[idx] :
                    return False
                
        if self.name != other.name :
            return False
        
        # TODO : check macro containment
        return True

