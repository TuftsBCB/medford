from enum import Enum
import re
from typing import List, Optional, Tuple

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

    macro_locations: Optional[List[Tuple[int, int, str]]] = None # replace with class?
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
    def find_macro_uses(line:str) -> List[Tuple[int,int]] :
        locations = []
        all_poss_comments = re.finditer(detail_statics.macro_use_regex, line)
        for match in all_poss_comments:
            locations.append((match.start(), match.end()))
        return locations

    @staticmethod
    def find_possible_latex(line:str) -> List[Tuple[int,int]] :
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
    def determine_macro_latex_overlap(line:str, poss_tex:List[Tuple[int,int]], poss_com:List[int]) -> Tuple[bool, List[Tuple[int,int]], bool, int] :
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

        poss_comments = linereader.find_possible_inline_comments(detail.line) if has_comment else []
        poss_latex = linereader.find_possible_latex(detail.line) if has_latex else []
        poss_macros = linereader.find_macro_uses(detail.line) if has_macros else []

        finalized_comment = -1
        finalized_tex = []
        finalized_macros = []

        if has_comment and has_latex :
            has_latex, finalized_tex, has_comment, finalized_comment = linereader.determine_macro_latex_overlap(detail.line, poss_latex, poss_comments)


        if linereader.contains_macro_use(detail.line) :
            pass

        return detail
