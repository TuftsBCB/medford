import pytest
from MEDFORD.objs.lines import ContinueLine
from MEDFORD.medford_linereader import linereader
            
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
        assert linereader.contains_latex_use(ex_str)
        assert linereader.contains_inline_comment(ex_str)

        poss_comments = linereader.find_possible_inline_comments(ex_str)
        assert len(poss_comments) > 0

        poss_latex = linereader.find_possible_latex(ex_str)
        assert len(poss_latex) == 2

        test_obj = ContinueLine(0, ex[i], poss_comments, poss_latex, [])

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