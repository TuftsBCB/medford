import re
from typing import Tuple, List, Optional
from MEDFORD.objs.lines import Line, MacroLine, CommentLine, NovelDetailLine, ContinueLine

Macro = Tuple[int, int, str]
Tex = Tuple[int, int]

class detail_statics():
    macro_header:str = "`@"
    comment_header:str = "#"
    token_header:str = "@"
    _latex_marker:str = "$$"
    escaped_lm:str = re.escape(_latex_marker)

    major_minor_reg:str = "{}(?P<major>[A-Za-z_]+)(-(?P<minor>[A-Za-z]+))?\\s".format(token_header)

    # TODO: make macro name regex reusable
    macro_use_regex:str = "((?P<r1>{}\\{{(?P<mname_closed>[a-zA-Z0-9_]+)\\}})|(?P<r2>{}(?P<mname_open>[a-zA-Z0-9]+))(\\s|$|\\}}))".format(macro_header, macro_header)
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
    def find_macro_name_body(line:str) -> Tuple[str, str] :
        m = re.match("{}(?P<mname>[A-Za-z0-9_]+)\\s(?P<mbody>.+)$".format(detail_statics.macro_header), line)
        if m is not None :
            return (m.group('mname'), m.group('mbody'))
        else :
            raise ValueError("Attempted to find macro name and body on an invalid string: {}".format(line))

    @staticmethod
    def is_novel_token_line(line:str) -> bool :
        return re.match("{}[A-Za-z]".format(detail_statics.token_header), line) is not None

    @staticmethod
    def get_major_minor(line:str) -> Tuple[List[str], str, str] :
        mm_res: Optional[re.Match[str]] = re.match(detail_statics.major_minor_reg, line)
        if mm_res == None :
            raise NotImplementedError("Something went horribly wrong trying to find Major and Minor tokens.")
        else :
            mm_match_res : re.Match[str] = mm_res
            match_grps = mm_match_res.groupdict()

            major_res : List[str] = match_grps['major'].split("_")
            if 'minor' in match_grps.keys() :
                minor_res : str = match_grps['minor']
            else :
                minor_res : str = ""

            rest_of_line = line[mm_match_res.end():]
            return(major_res, minor_res, rest_of_line)
        
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
            if match.group('r1') is not None :
                locations.append((match.start('r1'), match.end('r1'), match.group('mname_closed')))
            else :
                locations.append((match.start('r2'), match.end('r2'), match.group('mname_open')))
        return locations

    @staticmethod
    def find_possible_latex(line:str) -> List[Tex] :
        locations = []
        all_poss_comments = re.finditer(detail_statics.latex_use_regex, line)
        for match in all_poss_comments:
            locations.append((match.start(), match.end()))
        return locations
    
    @staticmethod 
    def process_line(line: str, lineno: int) -> Optional[Line] :
        if line.strip() == "" :
            return None
        
        if LineReader.is_comment_line(line) :
            return CommentLine(lineno, line)
        else :
            poss_inline = LineReader.find_possible_inline_comments(line)
            poss_tex = LineReader.find_possible_latex(line)
            poss_macro = LineReader.find_macro_uses(line)

            if LineReader.is_macro_def_line(line) :
                mname, mbody = LineReader.find_macro_name_body(line)
                return MacroLine(lineno, line, mname, mbody, poss_inline, poss_tex, poss_macro)
            elif LineReader.is_novel_token_line(line) :
                major_str, minor_str, rest_of_line = LineReader.get_major_minor(line)
                return NovelDetailLine(lineno, line, major_str, minor_str, rest_of_line, poss_inline, poss_tex, poss_macro)
            else :
                return ContinueLine(lineno, line, poss_inline, poss_tex, poss_macro)
