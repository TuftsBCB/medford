from typing import List, Tuple


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
    has_inline: bool = False
    has_tex: bool = False
    has_macros: bool = False

    comm_str: str = ""
    comm_loc: int = -1
    tex_locs: List[Tuple[int, int]] = []
    macro_uses: List[Tuple[int,int,str]] = []

    def resolve_comm_tex_macro_logic(self, poss_com: List[int], poss_tex: List[Tuple[int,int]], poss_macro: List[Tuple[int,int,str]]) -> None :
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



#################################
# Classes                       #
#################################

class Line() :
    lineno: int
    line: str

    def __init__(self, lineno : int, line : str) :
        self.lineno = lineno
        self.line = line

class CommentLine(Line) :
    def __init__(self, lineno: int, line: str) :
        super(CommentLine, self).__init__(lineno, line)
    # TODO : complete

class MacroLine(ContentMixin, Line) :
    macro_name: str
    macro_content: str

    def __init__(self, lineno: int, line: str, poss_inline, poss_tex, poss_macro) :
        super(MacroLine, self).__init__(lineno, line)

        # [1:] is to skip the macro that this line itself is defining
        self.resolve_comm_tex_macro_logic(poss_inline, poss_tex, poss_macro[1:])

class NovelDetailLine(ContentMixin, Line) :
    major_tokens: List[str]
    minor_token: str
    payload: str

    # TODO : complete
    def __init__(self, lineno: int, line: str, majors: List[str], minor: str, payload: str, poss_inline, poss_tex, poss_macro) :
        super(NovelDetailLine, self).__init__(lineno, line)
        self.major_tokens = majors
        self.minor_token = minor
        self.payload = payload

        self.resolve_comm_tex_macro_logic(poss_inline, poss_tex, poss_macro)

class ContinueLine(ContentMixin, Line) :
    payload: str
    # TODO : complete
    def __init__(self, lineno: int, line: str, poss_inline, poss_tex, poss_macro) :
        super(ContinueLine, self).__init__(lineno, line)
        self.payload = line
        
        self.resolve_comm_tex_macro_logic(poss_inline, poss_tex, poss_macro)
