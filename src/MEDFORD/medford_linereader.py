from enum import Enum
import re
from typing import List, Optional, Tuple, TypeVar

# Given a line, needs to figure out what the line represents.
# Possible types:
#   Line        -> `@Mname M
#               -> #[.]+
#               -> @Tokens Payload
#               -> Payload
#               -> \n
#   Mname       -> [A-Za-z]+
#   M           -> M' Comment
#               -> M'
#   M'          -> M' Latex M'
#               -> Content
#   Content     -> [^($$)#]+
#   Comment     -> # [.]+
#   Latex       -> $$[^($$)]+$$
#   Tokens      -> Major
#               -> Major-Minor
#   Major       -> [A-Za-z_]+
#   Minor       -> [A-Za-z]+
#   Payload     -> A Comment
#               -> A
#   A           -> A Macro_Use A
#               -> A Latex A
#               -> Content
#   Macro_Use   -> `@{Mname}
#               -> `@Mname\s

# NOTE (s):
# - $$ is specifically to signify that a region is ONLY for LaTeX, we do not validate that it is proper LaTeX, and $$ can ONLY be used for these LaTeX regions

# NOTE :
# I think line-specific errors should be thrown here. Things such as:
#   - Invalid tokens (@Major-Minor-Minor2)
#   - No description (@Major-Minor\n)
#   - ???
# After verification/collection using the LineReader, MEDFORD passes them to the
#   detailparser to turn them into details, and there the more complex errors
#   can be reported.

Macro = Tuple[int, int, str]
Tex = Tuple[int, int]
class detail_statics():
    macro_header:str = "`@"
    comment_header:str = "#"
    token_header:str = "@"
    _latex_marker:str = "$$"
    escaped_lm:str = re.escape(_latex_marker)

    macro_use_regex:str = "({}\\{{[a-zA-Z0-9_]+\\}}|{}[a-zA-Z0-9]+(\\s|$))".format(macro_header, macro_header)
    comment_use_regex:str = "(?=({}\\s.+))".format(comment_header)
    latex_use_regex:str = "{}[^({})]+{}".format(escaped_lm, escaped_lm, escaped_lm)

class LineReturn :

    class LineType(Enum) :
        UNDEF = 0
        COMMENT = 1
        MACRO_DEF = 2
        DETAIL = 3
        CONT = 4 # continuation from a prev. line
    
    linetype: LineType
    line: str
    lineno: List[int]
    
    # line features
    has_inline_comment: bool = False
    has_macro_use: bool = False
    has_LaTeX: bool = False

    macro_locations: Optional[List[Macro]] = None # replace with class?
    tex_locations: Optional[List[Tex]] = None
    comment_text: Optional[str] = None

    def __init__(self, inpLine:str, inpLineNo:int) :
        self.linetype = self.LineType.UNDEF
        self.line = inpLine
        self.lineno = [inpLineNo]
        pass

    def is_comment(self) -> bool:
        return self.linetype == self.LineType.COMMENT

    def is_macro_def(self) -> bool:
        return self.linetype == self.LineType.MACRO_DEF

    def is_detail(self) -> bool:
        return self.linetype == self.LineType.DETAIL

    def add_features(self,  poss_macros: Optional[List[Macro]] = None, 
                            poss_texs: Optional[List[Tex]] = None,
                            poss_comments: Optional[List[int]] = None) -> None:
        # I hate how this is set up. Is there a better way to strip the Optional tag from poss_?
        #   Can only reach the `if tmp_hastex and tmp_hascom` block if poss_comments poss_texs are not None,
        #   but it seems like there's no way to tell the type checker that and it's not smart enough
        #   to figure it out itself
        # 11 lines of code just to strip out the Optionals...
        tmp_hasmacro, tmp_hastex, tmp_hascom = False, False, False
        macros : List[Macro] = []
        texs : List[Tex] = []
        comments: List[int] = []
        commloc: int = 0

        if poss_macros != None :
            tmp_hasmacro = True
            macros = poss_macros
        if poss_texs != None :
            tmp_hastex = True
            texs = poss_texs
        if poss_comments != None :
            tmp_hascom = True
            comments = poss_comments

        # following two if blocks always set self.tex_locations, self.macro_locations as [] if there are none.
        # should this be changed so it sets it to None instead? not sure...
        # They're defaulted as Optional[..] types, so will need to always check anyways
        # predicted poss. fail state:
        #   - no valid tex locations
        #   - self.has_LaTeX = False
        #   - self.tex_locations = []
        #   - accidentally check if(self.has_inline_comment) instead
        #   - proceed on empty list
        #   quiet failure, kind of a concern
        if tmp_hastex and tmp_hascom :
            tmp_hastex, texs, tmp_hascom, commloc = LineReturn.determine_macro_latex_overlap(self.line, texs, comments)

            self.has_inline_comment = tmp_hascom
            self.comment_text = self.line[commloc:]
            self.line = self.line[:commloc]
            # TODO: test how this splits the line

            self.has_LaTeX = tmp_hastex
            self.tex_locations = texs
        elif tmp_hastex :
            # TODO : tests
            self.has_LaTeX = tmp_hastex
            self.tex_locations = texs
        elif tmp_hascom :
            # TODO : tests
            commloc = comments[0]
            self.has_inline_comment = tmp_hascom
            self.comment_text = self.line[commloc:]
            self.line = self.line[:commloc]

        if tmp_hasmacro and (tmp_hastex or tmp_hascom):
            tmp_hasmacro, macros = LineReturn.validate_macro_locs(texs if tmp_hastex else None, commloc if tmp_hascom else None, macros)

            self.has_macro_use = tmp_hasmacro
            self.macro_locations = macros
            # TODO: test... well, everything

        return
    
    @staticmethod
    def validate_macro_locs(poss_tex:Optional[List[Tex]], poss_com_loc:Optional[int], poss_macros: List[Macro]) -> Tuple[bool, List[Macro]]: 
        has_tex, has_comm = False, False
        tex_loc: List[Tex] = []
        com_loc: int = 0

        if poss_tex != None :
            has_tex = True
            tex_loc = poss_tex
        
        if poss_com_loc != None :
            has_comm = True
            com_loc = poss_com_loc

        finalized_macros: List[Macro] = []

        for macro in poss_macros :
            valid = True
            if has_tex :
                for tex in tex_loc :
                    if tex[0] < macro[0] and macro[1] < tex[1] :
                        # shouldn't be possible for a macro tail to go over the tex tail... $$ is not a valid macro name character
                        valid = False
                        break

            if has_comm :
                if macro[0] > com_loc :
                    valid = False

            if valid :
                finalized_macros.append(macro)

        return (len(finalized_macros) > 0, finalized_macros)
    
    @staticmethod
    def determine_macro_latex_overlap(line:str, poss_tex:List[Tex], poss_com:List[int]) -> Tuple[bool, List[Tex], bool, int] :
        """
        Determines which latex regions and which comment actually exist in a line.

        TODO: Maybe make this recursive? Also find a better way to type it -- the return type is horrifying..

        Parameters
        ----------
        line        str
            The line to analyze for tex, comment overlap.
        poss_tex    List[Tuple[int,int]]
            Locations of possible tex blocks within line; len(poss_com) > 0
        poss_com    List[int]
            Locations of possible inline comments within line; len(poss_com) > 0

        Returns
        -------
        Tuple[ bool, List[Tuple[int,int]], bool, int ]
        Tuple containing : whether there are valid tex blocks, the index ranges of those tex blocks, 
        whether there is a valid inline comment, and the location of that comment.
        """
        
        # check what the overlap is; make sure that the comment(s) is/aren't in a latex block, and
        #   ensure latex block isn't behind a comment
        com_i = 0
        tex_i = 0
        cur_com = poss_com[com_i]
        cur_tex = poss_tex[tex_i]
        finalized_comment = -1
        finalized_tex = []

        # I think there's an easier way to do this.
        # 1. for every poss. comment, starting from earliest:
        #   a. check if it's in a tex block
        #       i. if it is, move on to next comment starting from the same tex block
        #       ii. if it isn't, you're done
        # instead of doing the stuff below this should be doable in a for loop over (0, len(poss_com)),
        #   and using python cur_tex[0] < cur_com < cur_tex[1]

        while tex_i < len(poss_tex) :
            cur_com = poss_com[com_i]
            cur_tex = poss_tex[tex_i]
            if cur_com < cur_tex[0] :
                # comment is before tex, so this and later tex don't count
                finalized_comment = cur_com
                finalized_tex = poss_tex[:tex_i]
                break

            elif cur_com < cur_tex[1] :
                # comment in tex block
                if com_i < len(poss_com) -1 :
                    # go to next potential comment
                    com_i += 1
                else :
                    # no more next, no comments
                    finalized_tex = poss_tex
                    break

            else :
                # comment is after the tex we're looking at, get next tex
                tex_i += 1
                if tex_i >= len(poss_tex) :
                    # We're at the end, and nothing has collided with the current comment.
                    # Therefore, all possible latex are valid, and the current
                    #   comment we're looking at is the true comment.
                    finalized_comment = cur_com
                    finalized_tex = poss_tex
        
        ret_tex, ret_com = len(finalized_tex) > 0, finalized_comment > -1

        return (ret_tex, finalized_tex, ret_com, finalized_comment)

        
class linereader() :
    ## Methods to classify line type:
    # Comment
    # Macro definition
    # Novel token
    @staticmethod
    def is_comment_line(line:str) -> bool :
        return re.match("{}".format(detail_statics.comment_header), line) is not None

    @staticmethod
    def is_macro_def_line(line:str) -> bool :
        return re.match("{}[A-Za-z]".format(detail_statics.macro_header), line) is not None

    @staticmethod
    def is_novel_token_line(line:str) -> bool :
        return re.match("{}[A-Za-z]".format(detail_statics.token_header), line) is not None

    ## Methods to describe line attributes:
    # + Contains comment
    # + Uses a macro
    # + Contains LaTeX
    # NOTE: These are not functional independently. i.e. macro/LaTeX do not check that they are not in a comment
    @staticmethod
    def contains_inline_comment(line:str) -> bool :
        return re.search(detail_statics.comment_use_regex, line) is not None

    @staticmethod
    def contains_macro_use(line:str) -> bool :
        return re.search(detail_statics.macro_use_regex, line) is not None

    @staticmethod
    def contains_latex_use(line:str) -> bool:
        return re.search(detail_statics.latex_use_regex, line) is not None

    ## Methods to find specific locations of attributes
    @staticmethod
    def find_possible_inline_comments(line:str) -> List[int] :
        locations = []
        all_poss_comments = re.finditer(detail_statics.comment_use_regex, line)
        for match in all_poss_comments:
            locations.append(match.start())
        return locations

    @staticmethod
    def find_macro_uses(line:str) -> List[Macro] :
        locations = []
        all_poss_comments = re.finditer(detail_statics.macro_use_regex, line)
        for match in all_poss_comments:
            locations.append((match.start(), match.end()))
        return locations

    @staticmethod
    def find_possible_latex(line:str) -> List[Tex] :
        locations = []
        all_poss_comments = re.finditer(detail_statics.latex_use_regex, line)
        for match in all_poss_comments:
            locations.append((match.start(), match.end()))
        return locations
    
    ## Run line through all type, attribute testers
    @staticmethod
    def categorize_line(line:str, lineno:int) -> LineReturn:
        """
        Categorizes a line as a COMMENT, MACRO_DEF, DETAIL, or CONT.

        Parameters
        ----------
        line    : str
            input line to categorize
        lineno  : int
            line number of line from original MEDFORD file

        Returns
        -------
        LineReturn
            Line information object, with only line type set (inspectable using
            lr.linetype or lr.is_[comment|detail|macro_def] functions).

        Additional info
        ---------------
        Comment:        LineReturn.LineType.COMMENT
            Fulfills the requirements of linereader.is_comment_line
        Macro def:      LineReturn.LineType.MACRO_DEF
            Fulfills the requirements of linereader.is_macro_def_line
        Novel detail:   LineReturn.LineType.DETAIL
            Fulfills the requirements of linereader.is_novel_token_line
        Other:          LineReturn.LineType.CONT
            If a line fits no other requirements, it as assumed to be a
            continuation from another line.
        """
        lr = LineReturn(line, lineno)
        if linereader.is_comment_line(line) :
            lr.linetype = LineReturn.LineType.COMMENT
        elif linereader.is_macro_def_line(line) :
            lr.linetype = LineReturn.LineType.MACRO_DEF
        elif linereader.is_novel_token_line(line) :
            lr.linetype = LineReturn.LineType.DETAIL
        else :
            lr.linetype = LineReturn.LineType.CONT
        return lr

    @staticmethod
    def detail_features(detail:LineReturn) -> LineReturn:
        """
        Annotates a LineReturn with relevant features, such as comment location or latex locations, if relevant.

        Possible features:
            - Comment location and text
            - LaTeX locations and text
            - Macro usages locations and names

        Parameters
        ----------
        detail  LineReturn
            A LineReturn object.

        Returns
        -------
        LineReturn
            The same LineReturn as the input, but with features annotated.

        
        """
        has_comment = linereader.contains_inline_comment(detail.line)
        has_latex = linereader.contains_latex_use(detail.line)
        has_macros = linereader.contains_macro_use(detail.line)

        poss_comments = linereader.find_possible_inline_comments(detail.line) if has_comment else None
        poss_latex = linereader.find_possible_latex(detail.line) if has_latex else None
        poss_macros = linereader.find_macro_uses(detail.line) if has_macros else None

        detail.add_features(poss_macros, poss_latex, poss_comments)

        return detail
