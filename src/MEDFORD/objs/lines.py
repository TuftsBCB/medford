from typing import List, Tuple, Dict

# new plan:
# three ABCs, Line, Content, and Templateable
#   Line has lineno, int
#   Content has macro usage, inline comment, LaTeX
#   Templateable? has templates
# CommentLine subs Line
# MacroLine, ContinueLine, DetailLine subs Content
# ContinueLine, DetailLine subs Templateable

# new new plan:
# use mixins
# Line superclass: has lineno, int
# Content mixin: macro usage, inline comment, LaTeX
# Templateable mixin: has template functionality
# CommentLine subs Line
# MacroLine, ContinueLine, DetailLine use content mixin
# ContinueLine, DetailLine use templateable mixin

#################################
# Mixins                        #
#################################
class ContentMixin() :
    raw_content:str 

    offset: int = -1

    has_inline: bool = False
    has_tex: bool = False
    has_macros: bool = False

    comm_str: str = ""
    comm_loc: int = -1
    tex_locs: List[Tuple[int, int]] = []
    macro_uses: List[Tuple[int,int,str]] = []

    # TODO: is this the right place to put this?
    #           line is technically undefined...
    def _get_raw_content_offset(self) -> None:
        offset = self.line.find(self.raw_content)
        if offset == -1 :
            raise ValueError("Unable to find raw content in line")
        else :
            self.offset = offset

    def _offset_positions(self, poss_com: List[int], poss_tex: List[Tuple[int, int]], poss_macro: List[Tuple[int, int, str]]) -> Tuple[List[int], List[Tuple[int, int]], List[Tuple[int, int, str]]] :
        new_com = [x - self.offset for x in poss_com]
        new_tex = [(x - self.offset, y - self.offset) for (x,y) in poss_tex]
        new_macro = [(x - self.offset, y - self.offset, name) for (x,y,name) in poss_macro]
        return (new_com, new_tex, new_macro)

    def resolve_comm_tex_macro_logic(self, poss_com: List[int], poss_tex: List[Tuple[int,int]], poss_macro: List[Tuple[int,int,str]]) -> None :
        # adjust to raw_content positions
        self._get_raw_content_offset()
        (poss_com, poss_tex, poss_macro) = self._offset_positions(poss_com, poss_tex, poss_macro)

        if len(poss_com) > 0 and len(poss_tex) > 0 :
            self.deconvolute_comm_tex(poss_com, poss_tex)
        elif len(poss_com) > 0 :
            self.has_inline = True
            self.comm_loc = poss_com[0]
        elif len(poss_tex) > 0 :
            self.has_tex = True
            self.tex_locs = poss_tex

        if len(poss_macro) > 0 :
            self.find_macro_uses(poss_macro)

        return

    def recurse_comm_tex_overlap(self, poss_com: List[int], poss_tex: List[Tuple[int, int]]) -> Tuple[int, List[Tuple[int, int]]]:
        """
        Recursive helper function for deconvolute_comm_tex.
        """
        if len(poss_com) == 0 :
            return(-1, poss_tex)
        elif len(poss_tex) == 0 :
            return(poss_com[0], [])

        if poss_com[0] < poss_tex[0][0] :
            return (poss_com[0], [])

        elif poss_tex[0][0] < poss_com[0] < poss_tex[0][1] :
            return self.recurse_comm_tex_overlap(poss_com[1:], poss_tex)

        else :
            next_loop_ret = self.recurse_comm_tex_overlap(poss_com, poss_tex[1:])
            return (next_loop_ret[0], [poss_tex[0]] + next_loop_ret[1])

    def deconvolute_comm_tex(self, poss_com: List[int], poss_tex: List[Tuple[int, int]]) -> None :
        """
        If there are both potential inline comment(s) and potential LaTeX blocks, deconvolutes them to discover the 
        true inline comment location and LaTeX block locations.
        (e.g. if a TeX block is after a true inline comment, it does not consider that to be a true TeX block.)

        Parameters
        ----------
        poss_com (List[int]) : possible locations of an inline comment. 
        poss_tex (List[Tuple[int,int]]) : possible [start,end) locations of TeX blocks.

        Output
        ------
        None

        Side Effects
        ------------
        Sets has_inline, has_tex. \\
        If has_inline, sets comm_loc and comm_str, and adjusts line. \\
        If has_tex, sets tex_locs.

        Examples
        --------
        \\# inline $$ TeX $$ -> yes inline, no tex \\
        $$ TeX 1 $$ # inline $$ TeX 2$$ -> yes inline, one tex (first) \\
        $$ TeX # inline $$ -> no inline, one tex
        """
        results = self.recurse_comm_tex_overlap(poss_com, poss_tex)
        if results[0] == -1 :
            self.has_inline = False
        else :
            self.has_inline = True
            self.comm_loc = results[0]
            self.comm_str = self.line[results[0]:]
            self.line = self.line[:results[0]]

        if len(results[1]) == 0 :
            self.has_tex = False
        else :
            self.has_tex = True
            self.tex_locs = results[1]
    
    def recurse_macro_tex_overlap(self, poss_macro: List[Tuple[int, int, str]], poss_tex: List[Tuple[int,int]]) -> List[Tuple[int, int, str]] :
        if len(poss_macro) == 0 :
            return([])
        elif len(poss_tex) == 0 :
            return(poss_macro)
        
        elif poss_macro[0][0] < poss_tex[0][0] : # this macro is fine, move on to next MAC
            next_loop_ret = self.recurse_macro_tex_overlap(poss_macro[1:], poss_tex)
            return [poss_macro[0]] + next_loop_ret
        
        elif poss_tex[0][0] < poss_macro[0][0] < poss_tex[0][1] : # this macro invalid, move on to next MAC
            return self.recurse_macro_tex_overlap(poss_macro[1:], poss_tex)
        
        else : # don't know if macro is fine yet, move to next TEX
            return self.recurse_macro_tex_overlap(poss_macro, poss_tex[1:])

    def find_macro_uses(self, poss_macro: List[Tuple[int,int,str]]) -> None :
        ind_last : int = -1
        if self.has_inline :
            for i in range(0, len(poss_macro)) :
                if poss_macro[i][0] > self.comm_loc :
                    ind_last = i
                    break
        else :
            ind_last = len(poss_macro) - 1
        
        if ind_last >= 0 :
            if self.has_tex :
                # iterate thru
                deconv_results = self.recurse_macro_tex_overlap(poss_macro[:ind_last], self.tex_locs)
                if len(deconv_results) > 0 :
                    self.has_macros = True
                    self.macro_uses = deconv_results
            else :
                self.has_macros = True
                self.macro_uses = poss_macro[:ind_last+1]

    def replace_macros(self, macro_defs: Dict[str, str]) -> None :
        # TODO: add tests to make sure macro_uses is in first->last order
        if not self.has_macros or len(self.macro_uses) == 0 :
            raise ValueError("Attempted to replace macros in a line without macros.")

        n_macro_uses: int = len(self.macro_uses)
        for i in range(0, n_macro_uses) :
            cur_macro:Tuple[int,int,str] = self.macro_uses[n_macro_uses - i - 1]
            cur_macro_pos:Tuple[int,int] = (cur_macro[0],cur_macro[1])
            cur_macro_name:str = cur_macro[2]

            self.line = self.line[:cur_macro_pos[0]] + macro_defs[cur_macro_name] + self.line[cur_macro_pos[1]:]

    def get_content(self, macro_defs: Dict[str, str], remove_comments = True) -> str :
        if remove_comments :
            temp_content = self.remove_inline_comment()
        else :
            temp_content = self.raw_content

        if not self.has_macros or len(self.macro_uses) == 0 :
            return temp_content
        else :
            n_macro_uses: int = len(self.macro_uses)
            out = temp_content
            for i in range(0, n_macro_uses) :
                cur_macro:Tuple[int, int, str] = self.macro_uses[n_macro_uses - i - 1]
                cur_macro_pos: Tuple[int, int] = (cur_macro[0], cur_macro[1])
                cur_macro_name: str = cur_macro[2]

                out = out[:cur_macro_pos[0]] + macro_defs[cur_macro_name] + out[cur_macro_pos[1]:]

            return out
        
    def remove_inline_comment(self) -> str :
        if self.has_inline :
            return self.raw_content[:self.comm_loc].strip()
        else :
            return self.raw_content

                
        

#################################
# Classes                       #
#################################

class Line() :
    lineno: int
    line: str

    def __init__(self, lineno : int, line : str) :
        self.lineno = lineno
        self.line = line
    
    def __eq__(self, other) -> bool :
        if type(self) == type(other) :
            return self.line == other.line and self.lineno == other.lineno
        
        return False

    def get_lineno(self) -> int :
        return self.lineno

class CommentLine(Line) :
    def __init__(self, lineno: int, line: str) :
        super(CommentLine, self).__init__(lineno, line)

    def __eq__(self, other) -> bool :
        return super(CommentLine, self).__eq__(other)
    # TODO : complete

class MacroLine(ContentMixin, Line) :
    macro_name: str

    def __init__(self, lineno: int, line: str, macro_name:str, macro_body:str, poss_inline, poss_tex, poss_macro) :
        super(MacroLine, self).__init__(lineno, line)
        self.macro_name = macro_name
        self.raw_content = macro_body

        # [1:] is to skip the macro that this line itself is defining
        self.resolve_comm_tex_macro_logic(poss_inline, poss_tex, poss_macro[1:])
    
    def __eq__(self, other) -> bool:
        if type(self) == type(other) and self.macro_name == other.macro_name and \
            self.raw_content == other.raw_content :
            return super(MacroLine, self).__eq__(other)
        
        return False


class NovelDetailLine(ContentMixin, Line) :
    major_tokens: List[str]
    minor_token: str

    # TODO : complete
    def __init__(self, lineno: int, line: str, majors: List[str], minor: str, payload: str, poss_inline, poss_tex, poss_macro) :
        super(NovelDetailLine, self).__init__(lineno, line)
        self.major_tokens = majors
        self.minor_token = minor
        self.raw_content = payload

        self.resolve_comm_tex_macro_logic(poss_inline, poss_tex, poss_macro)

    def __eq__(self, other) -> bool :
        if type(self) == type(other) and self.major_tokens == other.major_tokens and \
            self.minor_token == other.minor_token and self.raw_content == other.raw_content :
            return super(NovelDetailLine, self).__eq__(other)
        
        return False

class AtAtLine(NovelDetailLine) :
    major_tokens: List[str]
    referenced_majors: List[str]

    def __init__(self, lineno: int, line: str, majors: List[str], referenced_majors: List[str], referenced_name: str, poss_inline, poss_tex, poss_macro):
        self.referenced_majors = referenced_majors
        pseudo_minor = "_".join(referenced_majors)
        super(AtAtLine, self).__init__(lineno, line, majors, pseudo_minor, referenced_name, poss_inline, poss_tex, poss_macro)

    def get_referenced_name(self, macro_defs: Dict[str, str]) -> str :
        return self.get_content(macro_defs)

class ContinueLine(ContentMixin, Line) :
    # TODO : complete
    def __init__(self, lineno: int, line: str, poss_inline, poss_tex, poss_macro) :
        super(ContinueLine, self).__init__(lineno, line)
        self.raw_content = line
        
        self.resolve_comm_tex_macro_logic(poss_inline, poss_tex, poss_macro)

    def __eq__(self, other) -> bool :
        if type(self) == type(other) and self.raw_content == other.raw_content :
            return super(ContinueLine, self).__eq__(other)
        
        return False
