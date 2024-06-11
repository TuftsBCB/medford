"""Manages the ingest and processing of strings from a MEDFORD text files. 
Handles functionality such as identifying Line types (comment, macro definition) 
and parsing line content, such as identifying the relevant Major and Minor tokens 
in a line. Eventually returns Line objects."""

import re
from typing import Tuple, List, Optional
from MEDFORD.submodules.mfdvalidator.errors import MissingAtAtName
from MEDFORD.objs.lines import Line, MacroLine, CommentLine, NovelDetailLine, ContinueLine

import MEDFORD.mfdglobals as mfdglobals

Macro = Tuple[int, int, str]
Tex = Tuple[int, int]

class DetailStatics():
    """Class that contains various static markers for reference across different functions in LineReader.
    Contains symbols such as the macro header symbol, which is used to determine whether a macro is being used and/or defined."""
    macro_header:str = "`@"
    comment_header:str = "#"
    token_header:str = "@"
    _latex_marker:str = "$$"
    escaped_lm:str = re.escape(_latex_marker) # ensures that the LaTeX symbol is parsed by regex correctly.

    # TODO : need to turn into f-strings carefully;
    #       have to check if I need to use f or fr to make sure \ work properly
    #       also, need to double all {} for them to be taken literally.
    major_minor_reg:str = "{}(?P<major>[A-Za-z_]+)(-(?P<minor>[A-Za-z]+))?\\s".format(token_header)

    # TODO: make macro name regex reusable
    macro_use_regex:str = "((?P<r1>{}\\{{(?P<mname_closed>[a-zA-Z0-9_]+)\\}})|(?P<r2>{}(?P<mname_open>[a-zA-Z0-9]+))(\\s|$|\\}}))".format(macro_header, macro_header)
    comment_use_regex:str = "(?=({}\\s.+))".format(comment_header)
    latex_use_regex:str = "{}[^({})]+{}".format(escaped_lm, escaped_lm, escaped_lm)
    atat_use_regex:str = "{}(?P<major>[A-Za-z_]+)-{}(?P<referenced>[A-Za-z_]+)(\\s(?P<name>.+))?$".format(token_header, token_header)

class LineReader :
    """Class that is used to identify line type, process strings, and return Line objects.
    All of the functions in this class are Static. Nothing requires instantiation.
    
    Contains functions such as `is_comment_line` and `get_major_minor`.
    
    Primary point of entry is the function `process_line`; everything else is mostly for use only within the LineReader class."""
    ## Methods to classify line type:
    # Comment
    # Macro definition
    # Novel token
    @staticmethod
    def is_comment_line(line:str) -> bool :
        """Returns True if the provided string is a comment line."""
        return re.match(f"{DetailStatics.comment_header}", line) is not None

    @staticmethod
    def is_macro_def_line(line:str) -> bool :
        """Returns True if the provided string is a macro definition line."""
        return re.match(f"{DetailStatics.macro_header}[A-Za-z]", line) is not None

    @staticmethod
    def is_atat_line(line:str) -> bool :
        """Returns True if the provided string is an At-At line."""
        return re.match(DetailStatics.atat_use_regex, line) is not None

    @staticmethod
    def find_macro_name_body(line:str) -> Tuple[str, str] :
        """Given a string, attempts to identify a macro name and its macro definition. If successful, returns them as a tuple."""
        m = re.match(f"{DetailStatics.macro_header}(?P<mname>[A-Za-z0-9_]+)\\s(?P<mbody>.+)$", line)
        if m is not None :
            return (m.group('mname'), m.group('mbody'))

        raise ValueError(f"Attempted to find macro name and body on an invalid string: {line}")

    @staticmethod
    def is_novel_token_line(line:str) -> bool :
        """Returns whether the line contains a novel MEDFORD token."""
        return re.match(f"{DetailStatics.token_header}[A-Za-z]", line) is not None

    @staticmethod
    def get_major_minor(line:str) -> Tuple[List[str], str, str] :
        """Given a line string, attempts to identify its major and minor tokens. 
        Returns a list of found major tokens, the minor token, and the line content.
        """
        mm_res: Optional[re.Match] = re.match(DetailStatics.major_minor_reg, line)
        if mm_res is None :
            raise NotImplementedError("Something went horribly wrong trying to find Major and Minor tokens.")
        else :
            mm_match_res : re.Match = mm_res
            match_grps = mm_match_res.groupdict()

            major_res : List[str] = match_grps['major'].split("_")
            if 'minor' in match_grps.keys() :
                minor_res : str = match_grps['minor']
            else :
                minor_res : str = ""

            rest_of_line = line[mm_match_res.end():]
            return(major_res, minor_res, rest_of_line)

    @staticmethod
    def get_atat_attr(line:str, lineno:int) -> Optional[Tuple[List[str], List[str], str]] :
        """Given a line and its line number, attempts to identify at-at attributes.
        
        DEPRECIATED, At-At is currently being reworked."""
        aa_res: Optional[re.Match] = re.match(DetailStatics.atat_use_regex, line)
        if aa_res is None :
            raise ValueError("Attempted to get @-@ attributes on a line that does not contain @-@ use.")
        else :
            aa_match_res : re.Match = aa_res
            match_grps = aa_match_res.groupdict()
            if match_grps['name'] is None :
                mfdglobals.validator.add_error(MissingAtAtName(match_grps['major'], match_grps['referenced'], lineno))
                return None

            major_res = match_grps['major'].split("_")
            referenced_res = match_grps['referenced'].split("_")
            return (major_res, referenced_res, match_grps['name'])

    ## Methods to describe line attributes:
    # + Contains comment
    # + Uses a macro
    # + Contains LaTeX
    # NOTE: These are not functional independently. i.e. macro/LaTeX do not check that they are not in a comment
    @staticmethod
    def contains_inline_comment(line:str) -> bool :
        """Returns True if the line contains an Inline comment."""
        return re.search(DetailStatics.comment_use_regex, line) is not None

    @staticmethod
    def contains_macro_use(line:str) -> bool :
        """Returns True if the line contains a macro usage."""
        return re.search(DetailStatics.macro_use_regex, line) is not None

    @staticmethod
    def contains_latex_use(line:str) -> bool:
        """Returns True if the line contains a LaTeX block."""
        return re.search(DetailStatics.latex_use_regex, line) is not None

    ## Methods to find specific locations of attributes
    @staticmethod
    def find_possible_inline_comments(line:str) -> List[int] :
        """Returns all possible locations of inline comments in a string line."""
        locations = []
        all_poss_comments = re.finditer(DetailStatics.comment_use_regex, line)
        for match in all_poss_comments:
            locations.append(match.start())
        return locations

    @staticmethod
    def find_macro_uses(line:str) -> List[Macro] :
        """Returns all possible macro uses in a string line."""
        locations = []
        all_poss_macros = re.finditer(DetailStatics.macro_use_regex, line)
        # Checks both possible macro use types, 'closed' (e.g. `@{macro}) and 'open' (e.g. `@macro)
        for match in all_poss_macros:
            if match.group('r1') is not None :
                locations.append((match.start('r1'), match.end('r1'), match.group('mname_closed')))
            else :
                locations.append((match.start('r2'), match.end('r2'), match.group('mname_open')))
        return locations

    @staticmethod
    def find_possible_latex(line:str) -> List[Tex] :
        """Returns all possible LaTeX blocks in a string line."""
        locations = []
        all_poss_comments = re.finditer(DetailStatics.latex_use_regex, line)
        for match in all_poss_comments:
            locations.append((match.start(), match.end()))
        return locations

    # TODO : move file reading/crunching into LineReader from the main Medford function,
    #       so we can more easily add different file operation types (line-by-line vs dumping into memory).
    #       May also become relevant when we start handling imports.

    @staticmethod
    def process_line(line: str, lineno: int) -> Optional[Line] :
        """Given a line string and its line number, attempts to create a Line object containing all of its features.
        
        Features include whether there is an inline comment and whether there are any LaTeX blocks.
        
        Output are Line objects of their relevant subclass, which includes `CommentLine`s, `MacroLine`s, `NovelDetailLine`s, and `ContinueLine`s.
        Currently only returns None in the case of an At-At line (which are currently being ignored entirely) or if the line is empty."""
        if line.strip() == "" :
            return None

        if LineReader.is_comment_line(line) :
            return CommentLine(lineno, line)

        poss_inline = LineReader.find_possible_inline_comments(line)
        poss_tex = LineReader.find_possible_latex(line)
        poss_macro = LineReader.find_macro_uses(line)

        if LineReader.is_macro_def_line(line) :
            mname, mbody = LineReader.find_macro_name_body(line)
            return MacroLine(lineno, line, mname, mbody, poss_inline, poss_tex, poss_macro)

        # atat is currently being redefined.
        if LineReader.is_atat_line(line) :
            return None
        #    res = LineReader.get_atat_attr(line, lineno)
        #    if res is not None :
        #        majors, referenced_major, referenced_name = res
        #        return AtAtLine(lineno, line, majors, referenced_major, referenced_name, poss_inline, poss_tex, poss_macro)
        #    else :
        #        return None

        if LineReader.is_novel_token_line(line) :
            major_str, minor_str, rest_of_line = LineReader.get_major_minor(line)
            return NovelDetailLine(lineno, line, major_str, minor_str, rest_of_line, poss_inline, poss_tex, poss_macro)

        return ContinueLine(lineno, line, poss_inline, poss_tex, poss_macro)
    # "syntax check" -> return whether line is valid MEDFORD
    #   -> "tell me all the syntax problems with this list of strings"
