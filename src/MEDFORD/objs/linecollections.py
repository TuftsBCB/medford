"""Module defining LineCollections and Blocks.

Module defining the LineCollection object, which conceptually contains
a collection of lines, and the Block object, which is a collection of Details. 
Line collections include objects such as Macros and Details (e.g. a Macro 
is defined as a MacroLine followed by 0 or more ContinueLines.)
"""

from typing import Optional, List, Dict, Tuple, Union
from MEDFORD.objs.lines import AtAtLine, ContinueLine, MacroLine, NovelDetailLine

from MEDFORD.submodules.mfdvalidator.errors import MissingDescError, MaxMacroDepthExceeded, AtAtReferencedDoesNotExist, MissingContent

import MEDFORD.mfdglobals as mfdglobals 

# create mixin for macro, named obj handling
# TODO: separate LineCollection into a LineCollection and FeatureContainer
class LineCollection() :
    """Class representing a collection of Lines.
    
    Class that is defined as a collection of Lines. It must contain a 
    headline, of type MacroLine or NovelDetailLine, which is used to define
    the type of LineCollection to create. It may also contain 0 or more 
    ContinueLines.
    
    A LineCollection contains collection-specific information, such as
    whether or not the collection has a macro usage (has_macro), and if so,
    the names of the macros that are used (used_macro_names) for easy
    management and validation later.
    """
    headline: Union[MacroLine, NovelDetailLine, AtAtLine]
    extralines: Optional[List[ContinueLine]]

    has_macros: bool = False
    used_macro_names: Optional[List[str]] = None

    def __init__(self, headline: Union[MacroLine, NovelDetailLine, AtAtLine], extralines: Optional[List[ContinueLine]]) :
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
        """Returns the string content of the LineCollection.
        
        Returns a plain string containing only the line collection's content.
        For a macro, this refers to the content that would get substituted in
        for the macro's name. For a detail, this would be the actual metadata
        content of the detail.
        
        Works by taking the content of the headline (with macros substituted
        for their content), and if there are any, does the same process for
        all of the extralines.
        
        Takes as input a dictionary containing all known macro names
        and their substitutions.
        """
        out : str = self.headline.get_content(resolved_macros)
        if self.extralines is not None :
            for line in self.extralines :
                out += line.get_content(resolved_macros)

        return out

    def get_linenos(self) -> List[int] :
        """Returns a list of line numbers of all lines in the LineCollection.
        """
        lines: List[int] = [self.headline.get_lineno()]
        if self.extralines is not None :
            for el in self.extralines :
                lines.append(el.get_lineno())
        return lines

    # pylint: disable=unused-argument
    # yes, pylint, I know these aren't used. Temporary while atat is disabled.
    def validate_atat(self, macro_defs: Dict[str, str], named_blocks: List[str]) -> bool :
        """
        TEMPORARILY DISABLED: ALWAYS RETURNS TRUE
        
        Validates that all At-At references within the line have been defined.
        """
        return True
    # pylint: enable=unused-argument

    # add type annotations?
    def __eq__(self, other) -> bool :
        if not isinstance(other, type(self)):
            return False

        if self.headline != other.headline :
            return False

        if self.has_macros != other.has_macros :
            return False

        if self.has_macros and self.used_macro_names is not None and other.used_macro_names is not None:
            for idx, mn in enumerate(self.used_macro_names) :
                if mn != other.used_macro_names[idx] :
                    return False

        if (self.extralines is None) ^ (other.extralines is None) :
            return False

        if self.extralines is not None and other.extralines is not None:
            if len(self.extralines) != len(other.extralines) :
                return False

            for idx, line in enumerate(self.extralines) :
                if line != other.extralines[idx] :
                    return False

        return True


class Macro(LineCollection) :
    """Subclass of LineCollection that represents a Macro.
    """
    name : str
    _is_resolved: bool = False
    _n_resolutions: int
    _deepest_res_macro: Optional['Macro'] = None
    resolution: str

    MAX_DEPTH: int = 10

    def __init__(self, headline: MacroLine, extralines: Optional[List[ContinueLine]]):
        super(Macro, self).__init__(headline, extralines)
        self.name = headline.macro_name

    def get_raw_content(self) -> str :
        """Returns the raw substitution string of the macro.

        Specifically, returns the exact string content of the macro,
        without attempting to substitute for referenced macro names or
        other post-processing.
        """
        outstr = self.headline.raw_content
        if self.extralines is not None :
            for el in self.extralines :
                outstr = outstr + el.raw_content
        return outstr

    def resolve(self, macro_definitions: Dict[str, 'Macro'], depth: Optional[int] = None) -> Union[str, List['Macro']] :
        """Resolve the content of the macro, up to 10 recursions.

        Given a list of macros that have currently been defined, and the
        current recursion depth of resolution, either returns the resolved
        macro string or, in failure case, a list of all macros that were
        used to reach failure.
        """
        # TODO : add a new way to track max resolutions.
        if depth is None :
            cdepth: int = 0
        else :
            cdepth: int = depth

        print(self.name)
        print(cdepth)

        if self._is_resolved :
            return self.resolution

        if cdepth == Macro.MAX_DEPTH :
            return [self]

        if not self.has_macros :
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
                        mfdglobals.validator.add_error(MaxMacroDepthExceeded(r))
                        return "ERROR"

                    return r

                # macro resolved successfully
                if isinstance(r, str) :
                    resolved_macros[m] = r
                    cur_res_depth = macro_definitions[m]._n_resolutions + 1
                    if cur_res_depth > deepest_resolution :
                        deepest_resolution = cur_res_depth
                        deepest_macro = macro_definitions[m]

                else :
                    raise TypeError(f"Unknown type returned from Macro.resolve(): {type(r).__name__}")

            self._n_resolutions = deepest_resolution
            self._deepest_res_macro = deepest_macro

            if self._n_resolutions == Macro.MAX_DEPTH :
                mfdglobals.validator.add_error(MaxMacroDepthExceeded(self._get_resolution_chain()))
                return 'ERROR'

            res = self.get_content(resolved_macros)
            self._is_resolved = True
            self.resolution = res
            return res

        raise ValueError("Somehow has_macros is True but used_macro_names is None.")

    def _get_resolution_chain(self) -> List['Macro'] :
        tmp : List['Macro'] = [self]
        if self._deepest_res_macro is not None :
            tmp.append(self._deepest_res_macro)
        return tmp

    def __eq__(self, other) -> bool :
        if isinstance(other, type(self)) and self.name == other.name:
            return super().__eq__(other)

        return False


# TODO: create 'HasMajors' mixin
class Detail(LineCollection) :
    """Class that represents a collection of Lines that form a Detail.
    """
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
        super(Detail, self).__init__(headline, extralines)

        # find major, minor tokens from first line
        self.major_tokens = headline.major_tokens
        self.minor_token = headline.minor_token

        if self.minor_token is None :
            self.is_header = True
        else :
            self.is_header = False

        content_length = len(self.headline.raw_content.strip())
        if self.extralines is not None :
            for line in self.extralines :
                content_length = content_length + len(line.raw_content.strip())

        if content_length == 0 :
            mfdglobals.validator.add_error(MissingContent(self))


    def get_str_majors(self) -> str :
        """Returns the list of major tokens as a _-joined string.
        """
        return "_".join(self.major_tokens)

    def get_raw_content(self) -> str :
        """Returns the content of the Detail, as a string without substitutions.
        """
        out = str.strip(self.headline.raw_content)
        if self.extralines is not None :
            for line in self.extralines :
                out = out + " " + str.strip(line.raw_content)
        return out

    def get_content(self, resolved_macros: Dict[str, str]) -> str :
        out = self.headline.get_content(resolved_macros)
        if self.extralines is not None :
            for line in self.extralines :
                out = out + line.get_content(resolved_macros)
        out = out.strip()
        return out

    def __eq__(self, other) -> bool :
        if isinstance(other, type(self)) :
            if self.major_tokens == other.major_tokens and self.is_header == other.is_header :
                if (self.minor_token is None) ^ (other.minor_token is None) :
                    return False

                if self.minor_token != other.minor_token :
                    return False

                return super().__eq__(other)

        return False

class AtAt(Detail) :
    """DEPRECIATED.
    
    (Used to) represent a detail that contains a reference to a block."""
    major_tokens: List[str]
    minor_token: str
    referenced_majors: List[str]
    is_header: bool = False

    def __init__(self, headline: AtAtLine, extralines: Optional[List[ContinueLine]]):
        super(Detail, self).__init__(headline, extralines)
        self.major_tokens = headline.major_tokens
        self.referenced_majors = headline.referenced_majors
        self.minor_token = "_".join(headline.referenced_majors)

    def get_referenced_str_majors(self) -> str :
        return "_".join(self.referenced_majors)

    def _get_referenced_name(self, macro_defs: Dict[str, str]) -> str :
        temp_name = self.minor_token + "@" + self.headline.get_content(macro_defs)
        if self.extralines is not None :
            for line in self.extralines :
                temp_name += line.get_content(macro_defs)
        return temp_name

    def validate_atat(self, macro_defs: Dict[str, str], named_blocks: List[str]) -> bool:
        referenced_name = self._get_referenced_name(macro_defs)
        if referenced_name not in named_blocks :
            mfdglobals.validator.add_error(AtAtReferencedDoesNotExist(self, referenced_name, named_blocks))
        return self._get_referenced_name(macro_defs) in named_blocks

class Block() :
    """
    A named collection of Details.
    
    A Block represents the entirety of all Details that cohesively describe
    a single object, the type of which is defined by the major tokens.
    
    Has features such as the defining major token, all defined minor tokens,
    the head Detail that is the start of the block, any other details
    describing the same object, and whether any macros have been used.
    """
    major_tokens: List[str]
    minor_tokens: Optional[List[Tuple[str, Detail]]] # Technically can have MFD block with nothing but a name
    details: List[Detail]
    head_detail: Detail

    has_atat: bool
    atat_references: Optional[List[int]] # ?

    name: str

    has_macros: bool = False
    used_macro_names: Optional[List[str]] = None

    atats : List[str]

    def __init__(self, details: List[Detail]) :
        if len(details) == 0 :
            raise ValueError("Attempted to create a block with no details.")

        self.details = details
        # ?
        self.major_tokens = details[0].major_tokens
        if details[0].minor_token is not None and details[0].minor_token != "" :
            mfdglobals.validator.add_error(MissingDescError(details[0]))
            #raise ValueError("No desc line for first detail provided to Block constructor.")
        self.head_detail = details[0]
        self.name = details[0].get_raw_content().strip()

        if len(details) > 0 :
            self.minor_tokens = []
            for idx, detail in enumerate(details[1:]) :
                if detail.major_tokens != self.major_tokens :
                    my_majors_str = "_".join(self.major_tokens)
                    detail_majors_str = "_".join(detail.major_tokens)
                    raise ValueError(f"Block provided details of multiple major tokens: Block Major is {my_majors_str} while line {idx} has major of {detail_majors_str}.")
                if detail.minor_token is None :
                    raise ValueError(f"Block provided a detail with no minor token past first detail: detail # {idx}.")

                self.minor_tokens.append((detail.minor_token, detail))

                #if detail

                if detail.has_macros and detail.used_macro_names is not None :
                    if self.used_macro_names is None :
                        self.used_macro_names = []
                        self.has_macros = True

                    for macro_use in detail.used_macro_names :
                        if macro_use not in self.used_macro_names :
                            self.used_macro_names.append(macro_use)

    def get_str_major(self) -> str :
        """Returns the Block's major tokens as a _-joined string.
        """
        return "_".join(self.major_tokens)

    def __eq__(self, other) -> bool :
        if not isinstance(other, type(self)) :
            return False

        if self.major_tokens != other.major_tokens :
            return False

        if (self.minor_tokens is None) ^ (other.minor_tokens is None) :
            return False

        elif self.minor_tokens is not None and other.minor_tokens is not None :
            if len(self.minor_tokens) != len(other.minor_tokens) :
                return False
            else :
                for idx, t in enumerate(self.minor_tokens) :
                    if t != other.minor_tokens[idx] :
                        return False

        if len(self.details) != len(self.details) :
            return False

        for idx, d in enumerate(self.details) :
            if d != other.details[idx] :
                return False

        if self.name != other.name :
            return False

        # TODO : check macro containment
        return True
    
    def get_linenos(self) -> List[int] :
        """Returns the line numbers of all Details in this Block.
        """
        tmp_linenos: List[int] = []
        for d in self.details :
            tmp_linenos.extend(d.get_linenos())
        return tmp_linenos

    def validate_atat(self, macro_defs: Dict[str, str], named_blocks : Dict[str, 'Block']) -> bool :
        """DEPRECIATED.
        """
        block_names_only = []
        block_names_only.extend(named_blocks.keys())

        for d in self.details :
            if isinstance(d, AtAt) :
                d_atat : AtAt = d
                if not d.validate_atat(macro_defs, block_names_only) :
                    return False

            if not d.validate_atat(macro_defs, block_names_only) :
                return False

        return True

