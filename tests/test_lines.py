from MEDFORD.objs.lines import ContinueLine, MacroLine, NovelDetailLine
from MEDFORD.objs.linereader import LineReader
            
def test_separate_tex_comment() :
    ex = [("@Major-minor $$block 1$$ and $$ block 2 $$ and # a comment", (True, [(13,24), (29,42)], True, 47)),
        ("@Major-minor $$block 1$$ and $$ block # 2 $$ and # a comment", (True, [(13,24), (29,44)], True, 49)),
        ("@Major-minor $$block 1$$ and $$ block # 2 $$ and no comment", (True, [(13, 24), (29,44)], False, -1)),

        ("@Major-minor $$block 1$$ and # a comment $$ block 2 $$", (True, [(13, 24)], True, 29)),
        ("@Major-minor $$block 1$$ and # a comment $$ block 2 $$ # and a second comment", (True, [(13, 24)], True, 29)),

        ("@Major-minor $$block # comment 1$$ and $$ block 2 $$", (True, [(13, 34), (39, 52)], False, -1)),
        ("@Major-minor $$block # comment 1$$ and # a comment and $$ block 2 $$", (True, [(13, 34)], True, 39)),
        
        ("@Major-minor # a commented $$block 1$$ and $$ block 2 $$", (False, [], True, 13))]

    for i in range(0, len(ex)) :
        ex_str = ex[i][0]
        ex_sol = ex[i][1]
        assert LineReader.contains_latex_use(ex_str)
        assert LineReader.contains_inline_comment(ex_str)

        poss_comments = LineReader.find_possible_inline_comments(ex_str)
        assert len(poss_comments) > 0

        poss_latex = LineReader.find_possible_latex(ex_str)
        assert len(poss_latex) == 2

        test_obj = ContinueLine(0, ex[i][0], poss_comments, poss_latex, [])

        has_tex = test_obj.has_tex
        assert has_tex == ex_sol[0]

        if has_tex :
            tex = test_obj.tex_locs
            assert tex == ex_sol[1]

        has_comm = test_obj.has_inline
        assert has_comm == ex_sol[2]

        if has_comm :
            comm = test_obj.comm_loc
            assert comm == ex_sol[3]


#########################################
# Macro definition line tests           #
#########################################
def test_MacroLine_FindMacro_UseMacro() :
    test_line = "`@Macro def `@MacroUse"
    lr = LineReader.process_line(test_line, -1)
    assert isinstance(lr, MacroLine)
    assert lr.has_macros
    assert lr.macro_uses[0] == (4,14,"MacroUse")

def test_MacroLine_FindMacro_UseMacro_Curly() :
    test_line = "`@Macro def `@{MacroUse}"
    lr = LineReader.process_line(test_line, -1)
    assert isinstance(lr, MacroLine)
    assert lr.has_macros
    assert lr.macro_uses[0] == (4,16, "MacroUse")

def test_MacroLine_FindMacro_NoUseMacro() :
    test_line = "`@Macro def"
    lr = LineReader.process_line(test_line, -1)
    assert isinstance(lr, MacroLine)
    assert not lr.has_macros

def testMacroLine_FindMacro_UseTwoMacro() :
    test_line = "`@Macro def `@MacroUse1 `@MacroUse2"
    lr = LineReader.process_line(test_line, -1)
    assert isinstance(lr, MacroLine)
    assert lr.has_macros
    assert len(lr.macro_uses) == 2
    assert lr.macro_uses[0] == (4,15,"MacroUse1")
    assert lr.macro_uses[1] == (16,27,"MacroUse2")

#########################################
# Novel detail line tests               #
#########################################

def test_NovelDetailLine_FindMacro_UseMacro() :
    test_line = "@Major-minor `@MacroUse"
    lr = LineReader.process_line(test_line, -1)
    assert isinstance(lr, NovelDetailLine)
    assert lr.has_macros
    assert len(lr.macro_uses) == 1
    assert lr.macro_uses[0] == (0,10,"MacroUse")
    
from typing import List, Optional
from MEDFORD.objs.lines import Line
class Macro_Replacement_Tests :
    def setup_method(self) :
        macro_strs: List[str] = [
            "`@Macro1 definition",
            "`@Macro2 `@Macro1",
            "`@Macro3 `@{Macro1}",
            "`@Macro4 `@Macro2",
            "`@Macro5 `@Macro2 asdf"
        ]

        macro_lines: List[Line] = []

        for idx,l in enumerate(macro_strs) :
            r: Optional[Line] = LineReader.process_line(l, idx)
            if r is not None :
                macro_lines.append(r)

        raise NotImplementedError()

    def test_basic_replacement(self) :
        raise NotImplementedError()