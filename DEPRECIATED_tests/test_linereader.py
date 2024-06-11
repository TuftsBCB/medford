import pytest

from MEDFORD.medford_linereader import *
@pytest.fixture
def general_context() :
    def generate_type_counts(dict_to_count, types) :
        counts = {}
        for t in types:
            inds = [int(name.split("_")[1]) for name in dict_to_count.keys() if re.search("^" + t + "_[0-9]+", name)]
            counts[t] = max(inds)
            inds = [int(name.split("_")[2]) for name in dict_to_count.keys() if re.search("invalid_" + t + "_[0-9]+", name)]
            counts["invalid_" + t] = max(inds)
        return counts

    example_lines = {
        "comment_1": "#Hello this is a comment",
        "comment_2": "# Hello this is a comment",
        "invalid_comment_1": "Hello this is #not a comment line",

        "macro_1": "`@Macro Line",
        "macro_2": "`@Macro Line With More Parts",
        "invalid_macro_1": "`@ Invalid MacroLine",

        "token_1": "@Major Token Line",
        "token_2": "@Major_Major2 Token Line",
        "token_3": "@Major-Minor Token Line",
        "token_4": "@Major_Major2-Minor Token Line",
        "invalid_token_1": "@ Incorrect Token line",
    }
    line_types = ["comment", "macro", "token"]
    line_counts = generate_type_counts(example_lines, line_types)

    example_inlines = {
        "comment_1": "Hello this is an # inline comment",
        "comment_2": "Hello this is # also an # inline comment",
        "comment_3": "Hello this should only # find one possible #inline comment",
        "invalid_comment_1": "Hello this is an #invalid inline comment",

        "macro_1": "Hello this is using a `@macro",
        "macro_2": "Hello this is using a `@macro ",
        "macro_3": "Hello this is using a `@{macro}",
        "macro_4": "Hello this is using a `@{macro}too",
        "macro_5": "Look, `@two `@macros !",
        "macro_6": "Look, `@two `@{macros}!",
        "macro_7": "Look, `@{two} `@{macros}!",
        "macro_8": "Look, `@{two} `@macros !",
        "invalid_macro_1": "Hello this is not using a `@ macro",

        "latex_1": "Hello this is using a $$latex$$ block.",
        "latex_2": "Hello this is using a $$latex block.$$",
        "latex_3": "Hello this is using a $$latex$$block.",
        "latex_4": "Hello there are $$two$$ $$latex$$ blocks.",
        "latex_5": "Hello there are also $$two$$ latex $$blocks$$ here.",
        "invalid_latex_1": "Hello this is does $$ not have a latex block.",
    }
    inline_types = ["comment", "macro", "latex"]
    inline_counts = generate_type_counts(example_inlines, inline_types)

    return {"example_lines": example_lines, "example_counts": line_counts, 
            "example_inlines": example_inlines, "inline_counts": inline_counts}

def test_detect_comment(general_context) :
    example_counts = general_context["example_counts"]
    example_lines = general_context["example_lines"]

    for key in example_counts.keys() :
        if key == "comment":
            for line_no in range(1,example_counts[key]+1 ) :
                assert linereader.is_comment_line(example_lines[key + "_" + str(line_no)])
        else :
            for line_no in range(1,example_counts[key]+1 ) :
                assert not linereader.is_comment_line(example_lines[key + "_" + str(line_no)])
    
def test_detect_macro(general_context) :
    example_counts = general_context["example_counts"]
    example_lines = general_context["example_lines"]

    for key in example_counts.keys() :
        if key == "macro":
            for line_no in range(1,example_counts[key]+1 ) :
                assert linereader.is_macro_def_line(example_lines[key + "_" + str(line_no)])
        else :
            for line_no in range(1,example_counts[key]+1 ) :
                assert not linereader.is_macro_def_line(example_lines[key + "_" + str(line_no)])

def test_detect_token(general_context) :
    example_counts = general_context["example_counts"]
    example_lines = general_context["example_lines"]

    for key in example_counts.keys() :
        if key == "token":
            for line_no in range(1,example_counts[key]+1 ) :
                assert linereader.is_novel_token_line(example_lines[key + "_" + str(line_no)])
        else :
            for line_no in range(1,example_counts[key]+1 ) :
                assert not linereader.is_novel_token_line(example_lines[key + "_" + str(line_no)])

def test_detect_inline_comment(general_context) :
    example_inlines = general_context["example_inlines"]
    inline_counts = general_context["inline_counts"]

    for key in inline_counts.keys() :
        if key == "comment":
            for line_no in range(1,inline_counts[key]+1 ) :
                assert linereader.contains_inline_comment(example_inlines[key + "_" + str(line_no)])
        elif key == "invalid_comment" :
            for line_no in range(1,inline_counts[key]+1 ) :
                assert not linereader.contains_inline_comment(example_inlines[key + "_" + str(line_no)])

def test_detect_macro_use(general_context) :
    example_inlines = general_context["example_inlines"]
    inline_counts = general_context["inline_counts"]

    for key in inline_counts.keys() :
        if key == "macro":
            for line_no in range(1,inline_counts[key]+1 ) :
                assert linereader.contains_macro_use(example_inlines[key + "_" + str(line_no)])
        elif key == "invalid_macro" :
            for line_no in range(1,inline_counts[key]+1 ) :
                assert not linereader.contains_macro_use(example_inlines[key + "_" + str(line_no)])

def test_detect_inline_latex(general_context) :
    example_inlines = general_context["example_inlines"]
    inline_counts = general_context["inline_counts"]

    for key in inline_counts.keys() :
        if key == "latex":
            for line_no in range(1,inline_counts[key]+1 ) :
                assert linereader.contains_latex_use(example_inlines[key + "_" + str(line_no)])
        elif key == "invalid_latex" :
            for line_no in range(1,inline_counts[key]+1 ) :
                assert not linereader.contains_latex_use(example_inlines[key + "_" + str(line_no)])

def test_find_comments(general_context) :
    example_inlines = general_context["example_inlines"]
    # comment_1 has on pos 17
    # comment_2 has on pos 14, 24
    # comment_3 has on pos 23
    locs = linereader.find_possible_inline_comments(example_inlines['comment_1'])
    assert len(locs) == 1
    assert 17 in locs

    locs = linereader.find_possible_inline_comments(example_inlines['comment_2'])
    assert len(locs) == 2
    assert 14 in locs
    assert 24 in locs

    locs = linereader.find_possible_inline_comments(example_inlines['comment_3'])
    assert len(locs) == 1
    assert 23 in locs
    
def test_find_latex(general_context) :
    example_inlines = general_context["example_inlines"]
    # tex 1 has on pos (22, 30)
    # tex 2 has on pos (22, 37)
    # tex 3 has on pos (22, 30)
    # tex 4 has on pos (16, 22), (24, 32)
    # tex 5 has on pos (21, 27), (35, 44)
    # +1 to end because it is including +1 character b/c ranges are usually end non-inclusive.
    correct_locs = [[(22, 31)],
                    [(22, 38)],
                    [(22, 31)],
                    [(16, 23), (24, 33)],
                    [(21, 28), (35, 45)]]
    for example in range(1,6) :
        locs = linereader.find_possible_latex(example_inlines['latex_' + str(example)])
        assert len(locs) == len(correct_locs[example - 1])
        for correct in correct_locs[example - 1] :
            assert correct in locs
    
def test_categorize_line(general_context) :
    example_counts = general_context["example_counts"]
    example_lines = general_context["example_lines"]

    for key in example_counts.keys() :
        if key == "comment":
            for line_no in range(1,example_counts[key]+1 ) :
                lr = linereader.categorize_line(example_lines[key + "_" + str(line_no)], -1)
                assert lr.linetype == LineReturn.LineType.COMMENT
        elif key == "macro" :
            for line_no in range(1,example_counts[key]+1 ) :
                lr = linereader.categorize_line(example_lines[key + "_" + str(line_no)], -1)
                assert lr.linetype == LineReturn.LineType.MACRO_DEF
        elif key == "token" :
            for line_no in range(1,example_counts[key]+1 ) :
                lr = linereader.categorize_line(example_lines[key + "_" + str(line_no)], -1)
                assert lr.linetype == LineReturn.LineType.DETAIL
        else :
            for line_no in range(1,example_counts[key]+1 ) :
                lr = linereader.categorize_line(example_lines[key + "_" + str(line_no)], -1)
                assert lr.linetype == LineReturn.LineType.CONT

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

        has_tex, tex, has_comm, comm = LineReturn.determine_macro_latex_overlap(ex[i], poss_latex, poss_comments)
        assert has_tex == ex_sol[0]
        assert tex == ex_sol[1]
        assert has_comm == ex_sol[2]
        assert comm == ex_sol[3]
        