from typing import Optional, List, Dict, Tuple, Union
from MEDFORD.objs.lines import Line, ContinueLine, ContentMixin, MacroLine, NovelDetailLine

from MEDFORD.submodules.medforderrors.errormanager import MedfordErrorManager as em
from MEDFORD.submodules.medforderrors.errors import MissingDescError, MaxMacroDepthExceeded

# create mixin for macro, named obj handling
# TODO: separate LineCollection into a LineCollection and FeatureContainer
class LineCollection() :
    headline: Union[MacroLine, NovelDetailLine]
    extralines: Optional[List[ContinueLine]]

    has_macros: bool = False
    used_macro_names: Optional[List[str]] = None

    def __init__(self, headline: Union[MacroLine, NovelDetailLine], extralines: Optional[List[ContinueLine]]) :
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

    def get_content(self, resolved_macros: Dict[str, str]) -> str :
        out : str = self.headline.get_content(resolved_macros)
        if self.extralines is not None :
            for l in self.extralines :
                out += l.get_content(resolved_macros)
        
        return out
    
    def get_linenos(self) -> List[int] :
        lines: List[int] = [self.headline.get_lineno()]
        if self.extralines is not None :
            for el in self.extralines :
                lines.append(el.get_lineno())
        return lines
    
    # add type annotations?
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
    _is_resolved: bool = False
    _n_resolutions: int
    _deepest_res_macro: Optional['Macro'] = None
    resolution: str

    def __init__(self, headline: MacroLine, extralines: Optional[List[ContinueLine]]):
        super(Macro, self).__init__(headline, extralines)
        self.name = headline.macro_name

    def get_raw_content(self) -> str :
        outstr = self.headline.raw_content
        if self.extralines is not None :
            for el in self.extralines :
                outstr = outstr + el.raw_content
        return outstr
    
    def resolve(self, macro_definitions: Dict[str, 'Macro'], depth: Optional[int] = None) -> Union[str, List['Macro']] :
        # TODO : add a new way to track max resolutions.
        if depth is None :
            cdepth: int = 0
        else :
            cdepth: int = depth
            
        if self._is_resolved : 
            return self.resolution
        
        if cdepth == 10 :
            return [self]
        
        if self.has_macros == False :
            self._is_resolved = True
            self.resolution = self.get_content({})
            self._n_resolutions = 0
            return self.resolution
        
        if self.used_macro_names is not None and len(self.used_macro_names) > 0:
            resolved_macros : Dict[str, str] = {}
            deepest_resolution : int = 0
            deepest_macro : Macro = self

            for m in self.used_macro_names :
                r = macro_definitions[m].resolve(macro_definitions, cdepth + 1)

                # error branch
                if isinstance(r, List) :
                    r.insert(0,self)
                    if cdepth == 0 :
                        em.instance().add_err(MaxMacroDepthExceeded(r))
                        return "ERROR"
                    else :
                        return r

                # macro resolved successfully
                elif isinstance(r, str) :
                    resolved_macros[m] = r
                    cur_res_depth = macro_definitions[m]._n_resolutions + 1
                    if cur_res_depth > deepest_resolution :
                        deepest_resolution = cur_res_depth
                        deepest_macro = macro_definitions[m]

                else :
                    raise TypeError("Unknown type returned from Macro.resolve(): %s" % type(r).__name__)
                
            self._n_resolutions = deepest_resolution
            self._deepest_res_macro = deepest_macro

            if self._n_resolutions == 10 :
                em.instance().add_err(MaxMacroDepthExceeded(self._get_resolution_chain()))
                return 'ERROR'

            res = self.get_content(resolved_macros)
            self._is_resolved = True
            self.resolution = res
            return res
        
        else :
            raise ValueError("Somehow has_macros is True but used_macro_names is None.")

    def _get_resolution_chain(self) -> List['Macro'] :
        tmp : List['Macro'] = [self]
        if self._deepest_res_macro is not None :
            tmp.append(self._deepest_res_macro)
        return tmp
    
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
        out = self.headline.get_content(macro_dict)
        if self.extralines is not None :
            for l in self.extralines :
                out = out + l.get_content(macro_dict)
        out = out.strip()
        return out

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
    headDetail: Detail

    name: str

    def __init__(self, details: List[Detail]) :
        if len(details) == 0 :
            raise ValueError("Attempted to create a block with no details.")
        
        self.details = details
        # ?
        self.major_tokens = details[0].major_tokens
        if details[0].minor_token is not None and details[0].minor_token != "" :
            em.instance().add_syntax_err(MissingDescError(details[0]))
            raise ValueError("No desc line for first detail provided to Block constructor.")
        self.headDetail = details[0]
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

    def get_content(self, defined_macros: Dict[str, str]) -> str :
        # TODO : I don't think this is currently ever called, because
        #   the dictionizer calls on a detail-per-detail basis. Is this
        #   function necessary?
        out = ""
        for detail in self.details :
            out = out + detail.get_content(defined_macros)
        return out

    def get_str_major(self) -> str :
        return "_".join(self.major_tokens)
    

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

