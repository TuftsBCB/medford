import re
from typing import Tuple, List
from MEDFORD.objs.lines import Line, MacroLine, CommentLine, NovelDetailLine, ContinueLine

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

class LineReader :
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
    
    @staticmethod 
    def process_line(line: str, lineno: int) -> Line :
        if LineReader.is_comment_line(line) :
            return CommentLine(lineno, line)
        else :
            poss_inline = LineReader.find_possible_inline_comments(line)
            poss_tex = LineReader.find_possible_latex(line)
            poss_macro = LineReader.find_macro_uses(line)
            if LineReader.is_macro_def_line(line) :
                return MacroLine(lineno, line, poss_inline, poss_tex, poss_macro)
            elif LineReader.is_novel_token_line(line) :
                return NovelDetailLine(lineno, line, poss_inline, poss_tex, poss_macro)
            else :
                return ContinueLine(lineno, line, poss_inline, poss_tex, poss_macro)
