from MEDFORD.objs.linecollector import LineCollector
from MEDFORD.objs.linereader import LineReader
from MEDFORD.objs.lines import AtAtLine, Line, ContinueLine, MacroLine, CommentLine, NovelDetailLine
from MEDFORD.objs.linecollections import Macro, Detail, Block
from typing import List, Dict

from typing import Optional


class TestLineCollection() :
    def setup_method(self, test_method) :
        pass

    #########################################
    # Single-Line Tests                     #
    #########################################


    def test_process_one_line_comment(self) :
        test_line: Optional[Line] = LineReader.process_line("#Comment", 0)
        assert test_line is not None

        confirmed_line : Line = test_line

        # TODO : do I like that you HAVE to create a LineCollector object?
        #           can't just call ProcessLines on its own?
        lc : LineCollector = LineCollector([confirmed_line])
        assert len(lc.named_blocks.keys()) == 0
        assert len(lc.defined_macros.keys()) == 0
        assert len(lc.comments) == 1
        assert lc.comments[0] == confirmed_line

    def test_process_one_line_macro(self) :
        test_line: Optional[Line] = LineReader.process_line("`@Macro value", 0)
        assert test_line is not None
        assert isinstance(test_line, MacroLine)

        confirmed_line : MacroLine = test_line

        lc : LineCollector = LineCollector([confirmed_line])
        assert len(lc.named_blocks.keys()) == 0
        assert len(lc.defined_macros.keys()) == 1
        assert len(lc.comments) == 0
        # TODO : expose this functionality in LineCollector so it can be called instead
        #           of reconstructed manually?
        assert lc.defined_macros[confirmed_line.macro_name] == Macro(confirmed_line, None)
        
    def test_process_one_line_detail(self) :
        test_line: Optional[Line] = LineReader.process_line("@Major NameOfBlock", 0)
        assert test_line is not None
        assert isinstance(test_line, NovelDetailLine)

        confirmed_line : NovelDetailLine = test_line

        lc : LineCollector = LineCollector([confirmed_line])
        assert len(lc.named_blocks.keys()) == 1
        assert len(lc.defined_macros.keys()) == 0
        assert len(lc.comments) == 0

        exdet = Detail(confirmed_line, None)
        blocks = lc._generate_blocks([exdet])

        assert len(blocks) == 1

        assert lc.named_blocks['Major']['NameOfBlock'] == blocks[0] 

    def test_process_one_line_detail_has_macro(self) :
        # Discovered I never actually flagged Details as having Macros.
        # This test ensures that a detail correctly has that flag set.
        test_line: Optional[Line] = LineReader.process_line("@Major-minor NameOfBlock `@macro", 0)
        assert test_line is not None
        assert isinstance(test_line, NovelDetailLine)

        confirmed_line : NovelDetailLine = test_line

        exdet = Detail(confirmed_line, None)
        assert exdet.has_macros == True
        assert exdet.used_macro_names == ['macro']

    #########################################
    # Two-Line Tests                        #
    #########################################

    def test_process_two_line_comment(self) :
        test_lines : List[str] = ["# Comment", " Continue"]
        test_Lines : List[Optional[Line]] = [LineReader.process_line(test_lines[0],0),
                                            LineReader.process_line(test_lines[1],1)]
        assert test_Lines[0] is not None
        assert test_Lines[1] is not None

        confirmed_lines : List[Line] = [test_Lines[0], test_Lines[1]]

        # TODO : this should throw a Medford error warning users that
        #       comments cannot 'roll over' to next line; they must
        #       be headed by a #?
        #       Either that, or LineCollector needs to be adjust &
        #       I need to create a Comment collection obj
        #lc : LineCollector = LineCollector(confirmed_lines)
        #assert len(lc.named_blocks.keys()) == 0
        #assert len(lc.defined_macros.keys()) == 0
        #assert len(lc.comments) == 1

    def test_process_two_line_macro(self) :
        test_lines : List[str] = ["`@Macro value", " continue"]
        test_Line_1 : Optional[Line] = LineReader.process_line(test_lines[0], 0)
        test_Line_2 : Optional[Line] = LineReader.process_line(test_lines[1], 1)

        assert test_Line_1 is not None
        assert isinstance(test_Line_1, MacroLine)
        confirmed_1 : MacroLine = test_Line_1

        assert test_Line_2 is not None
        assert isinstance(test_Line_2, ContinueLine)
        confirmed_2 : ContinueLine = test_Line_2

        lc : LineCollector = LineCollector([confirmed_1, confirmed_2])
        assert len(lc.named_blocks.keys()) == 0
        assert len(lc.defined_macros.keys()) == 1
        assert len(lc.comments) == 0

        # TODO : test that these constructors work as intended...
        ex_m = Macro(confirmed_1, [confirmed_2])
        assert lc.defined_macros['Macro'] == ex_m

    def test_process_two_line_detail(self) :
        test_lines : List[str] = ["@Major content", " continue"]
        test_Line_1 : Optional[Line] = LineReader.process_line(test_lines[0], 0)
        test_Line_2 : Optional[Line] = LineReader.process_line(test_lines[1], 1)

        assert test_Line_1 is not None
        assert isinstance(test_Line_1, NovelDetailLine)
        confirmed_1 : NovelDetailLine = test_Line_1

        assert test_Line_2 is not None
        assert isinstance(test_Line_2, ContinueLine)
        confirmed_2 : ContinueLine = test_Line_2

        lc : LineCollector = LineCollector([confirmed_1, confirmed_2])
        assert len(lc.named_blocks.keys()) == 1
        assert len(lc.defined_macros.keys()) == 0
        assert len(lc.comments) == 0

        # TODO : test that these constructors work as intended...
        ex_d = Detail(confirmed_1, [confirmed_2])
        ex_b = Block([ex_d])
        assert lc.named_blocks['Major']['content continue'] == ex_b

    def test_process_atat(self) :
        test_lines : List[str] = ["@Major content", "@Major-@MajorTwo Test"]
        test_Line_1 : Optional[Line] = LineReader.process_line(test_lines[0], 0)
        test_Line_2 : Optional[Line] = LineReader.process_line(test_lines[1], 1)

        assert test_Line_1 is not None
        assert isinstance(test_Line_1, NovelDetailLine)
        confirmed_1 : NovelDetailLine = test_Line_1

        assert test_Line_2 is not None
        assert isinstance(test_Line_2, AtAtLine)
        confirmed_2 : AtAtLine = test_Line_2

        # TODO : do I like that you HAVE to create a LineCollector object?
        #           can't just call ProcessLines on its own?
        lc : LineCollector = LineCollector([confirmed_1, confirmed_2])
        assert len(lc.named_blocks.keys()) == 1
        assert len(lc.defined_macros.keys()) == 0
        assert len(lc.comments) == 0
    #########################################
    # Multiple Of One Type Tests            #
    #########################################

    def test_two_comments(self) :
        test_lines : List[str] = ["#Comment 1", "# Comment 2"]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))

        confirmed_lines : List[CommentLine] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            assert isinstance(L, CommentLine)
            confirmed_lines.append(L)
        
        tmpinp : List[Line] = []
        tmpinp.extend(confirmed_lines)
        lc : LineCollector = LineCollector(tmpinp)

        assert len(lc.named_blocks.keys()) == 0
        assert len(lc.defined_macros.keys()) == 0
        assert len(lc.comments) == 2

        assert lc.comments == confirmed_lines

    def test_two_macros(self) :
        test_lines : List[str] = ["`@Macro1 value", "`@Macro2 value"]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))
        
        confirmed_lines : List[MacroLine] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            assert isinstance(L, MacroLine)
            confirmed_lines.append(L)

        tmpinp : List[Line] = []
        tmpinp.extend(confirmed_lines)

        lc : LineCollector = LineCollector(tmpinp)

        assert len(lc.named_blocks.keys()) == 0
        assert len(lc.defined_macros.keys()) == 2
        assert len(lc.comments) == 0

        assert lc.defined_macros['Macro1'] == Macro(confirmed_lines[0], None)
        assert lc.defined_macros['Macro2'] == Macro(confirmed_lines[1], None)

    def test_two_details(self) :
        test_lines : List[str] = ["@Major name", "@Major-Minor attr"]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))
        
        confirmed_lines : List[NovelDetailLine] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            assert isinstance(L, NovelDetailLine)
            confirmed_lines.append(L)

        tmpinp : List[Line] = []
        tmpinp.extend(confirmed_lines)

        lc : LineCollector = LineCollector(tmpinp)

        assert len(lc.named_blocks.keys()) == 1
        assert len(lc.defined_macros.keys()) == 0
        assert len(lc.comments) == 0
        
        details : List[Detail] = []
        for idx, c in enumerate(confirmed_lines) :
            details.append(Detail(c, None))
        ex_bl = Block(details)

        assert 'name' in lc.named_blocks['Major'].keys()
        assert lc.named_blocks['Major']['name'] == ex_bl
    
    #########################################
    # Multiline, Multiple One Type Tests    #
    #########################################

    def test_mult_poss_multiline_macros(self) :
        test_lines : List[str] = ["`@Macro1 stuff"," continue", "`@Macro2 morestuff", "`@Macro3 evenmore"]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))

        confirmed_lines : List[Line] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            confirmed_lines.append(L)

        lc : LineCollector = LineCollector(confirmed_lines)

        assert len(lc.named_blocks.keys()) == 0
        assert len(lc.defined_macros.keys()) == 3
        assert len(lc.comments) == 0

        assert 'Macro1' in lc.defined_macros.keys()
        assert 'Macro2' in lc.defined_macros.keys()
        assert 'Macro3' in lc.defined_macros.keys()

        assert isinstance(confirmed_lines[0], MacroLine)
        assert isinstance(confirmed_lines[1], ContinueLine)
        assert isinstance(confirmed_lines[2], MacroLine)
        assert isinstance(confirmed_lines[3], MacroLine)
        assert lc.defined_macros['Macro1'] == Macro(confirmed_lines[0], [confirmed_lines[1]])
        assert lc.defined_macros['Macro2'] == Macro(confirmed_lines[2], None)
        assert lc.defined_macros['Macro3'] == Macro(confirmed_lines[3], None)

    def test_mult_poss_multiline_details(self) :
        test_lines : List[str] = ["@Major name", " namecont", "@Major-minor firstminor", "@Major-minor secondminor", " secondcont"]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))
        
        confirmed_lines : List[Line] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            confirmed_lines.append(L)

        lc : LineCollector = LineCollector(confirmed_lines)

        assert len(lc.named_blocks.keys()) == 1
        assert len(lc.defined_macros.keys()) == 0
        assert len(lc.comments) == 0

        assert 'name namecont' in lc.named_blocks['Major'].keys()

        assert isinstance(confirmed_lines[0], NovelDetailLine)
        assert isinstance(confirmed_lines[1], ContinueLine)
        assert isinstance(confirmed_lines[2], NovelDetailLine)
        assert isinstance(confirmed_lines[3], NovelDetailLine)
        assert isinstance(confirmed_lines[4], ContinueLine)
        
        details = []
        details.append(Detail(confirmed_lines[0], [confirmed_lines[1]]))
        details.append(Detail(confirmed_lines[2]))
        details.append(Detail(confirmed_lines[3],[confirmed_lines[4]]))

        ex_bl = Block(details)

        assert lc.named_blocks['Major']['name namecont'] == ex_bl

    #########################################
    # Test Macro Resolution Capabilities    #
    #########################################

    # TODO: add these tests to a new file named test_obj_linecollections?
    def test_simple_macro_replace(self) :
        test_lines: List[str] = [
            "`@Macro value",
            "@Major `@Macro"
        ]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))

        confirmed_lines : List[Line] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            confirmed_lines.append(L)

        lc : LineCollector = LineCollector(confirmed_lines)
        assert len(lc.defined_macros.keys()) == 1
        resolved = lc.defined_macros["Macro"].resolve(lc.defined_macros)
        assert resolved == "value"

        blocks:List[Block] = lc.get_flat_blocks()
        assert len(blocks) == 1
        assert blocks[0].get_content({"Macro":resolved}) == "value" # type: ignore

    def test_multiline_macro_replace(self) :
        test_lines: List[str] = [
            "`@Macro value",
            " value 2",
            "@Major `@Macro"
        ]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))

        confirmed_lines : List[Line] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            confirmed_lines.append(L)

        lc : LineCollector = LineCollector(confirmed_lines)
        assert len(lc.defined_macros.keys()) == 1
        resolved = lc.defined_macros["Macro"].resolve(lc.defined_macros)
        assert resolved == "value value 2"

        blocks:List[Block] = lc.get_flat_blocks()
        assert len(blocks) == 1
        assert blocks[0].get_content({"Macro":resolved}) == "value value 2" # type: ignore

    def test_multilayer_macro_replace(self) :
        test_lines: List[str] = [
            "`@Macro1 value",
            "`@Macro2 `@Macro1",
            "@Major `@Macro2"
        ]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))

        confirmed_lines : List[Line] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            confirmed_lines.append(L)

        lc : LineCollector = LineCollector(confirmed_lines)
        assert len(lc.defined_macros.keys()) == 2
        resolved_macros : Dict[str, str] = {}
        for m in lc.defined_macros.keys() :
            resolved_macros[m] = lc.defined_macros[m].resolve(lc.defined_macros) # type: ignore
            
        assert resolved_macros['Macro1'] == "value"
        assert resolved_macros['Macro2'] == "value"

        blocks:List[Block] = lc.get_flat_blocks()
        assert len(blocks) == 1
        assert blocks[0].get_content(resolved_macros) == "value"
    
    def test_multilayer_macro_replace_3(self) :
        test_lines: List[str] = [
            "`@Macro1 value",
            "`@Macro2 21`@Macro1",
            "@Major 23`@Macro2"
        ]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))

        confirmed_lines : List[Line] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            confirmed_lines.append(L)

        lc : LineCollector = LineCollector(confirmed_lines)
        assert len(lc.defined_macros.keys()) == 2
        resolved_macros : Dict[str, str] = {}
        for m in lc.defined_macros.keys() :
            resolved_macros[m] = lc.defined_macros[m].resolve(lc.defined_macros) # type: ignore
            
        assert resolved_macros['Macro1'] == "value"
        assert resolved_macros['Macro2'] == "21value"

        blocks:List[Block] = lc.get_flat_blocks()
        assert len(blocks) == 1
        assert blocks[0].get_content(resolved_macros) == "2321value"
    
    def test_multilayer_macro_replace_2(self) :
        test_lines: List[str] = [
            "`@Macro1 value",
            "`@Macro2 21`@Macro1",
            "@Major 23`@{Macro2}32",
            "@Majortwo 23{`@Macro2}32"
        ]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))

        confirmed_lines : List[Line] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            confirmed_lines.append(L)

        lc : LineCollector = LineCollector(confirmed_lines)
        assert len(lc.defined_macros.keys()) == 2
        resolved_macros : Dict[str, str] = {}
        for m in lc.defined_macros.keys() :
            resolved_macros[m] = lc.defined_macros[m].resolve(lc.defined_macros) # type: ignore
            
        assert resolved_macros['Macro1'] == "value"
        assert resolved_macros['Macro2'] == "21value"

        blocks:List[Block] = lc.get_flat_blocks()
        assert len(blocks) == 2
        assert blocks[0].get_content(resolved_macros) == "2321value32"
        assert blocks[1].get_content(resolved_macros) == "23{21value}32"

    def test_multiline_multilayer_macro_replace(self) :
        test_lines: List[str] = [
            "`@Macro value",
            " value 2",
            "`@Macro2 hello",
            " `@Macro hello",
            " hello",
            "@Major `@Macro2"
        ]
        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))

        confirmed_lines : List[Line] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            confirmed_lines.append(L)

        lc : LineCollector = LineCollector(confirmed_lines)
        assert len(lc.defined_macros.keys()) == 2
        resolved_macros : Dict[str, str] = {}
        for m in lc.defined_macros.keys() :
            resolved_macros[m] = lc.defined_macros[m].resolve(lc.defined_macros) # type: ignore
        assert resolved_macros['Macro'] == "value value 2"
        assert resolved_macros['Macro2'] == "hello value value 2 hello hello"

        blocks:List[Block] = lc.get_flat_blocks()
        assert len(blocks) == 1
        assert blocks[0].get_content(resolved_macros) == "hello value value 2 hello hello"

    #########################################
    # Free-for-all. Yipee!                  #
    #########################################

    def test_go_ham(self) :
        # NOTE: test is a bit odd if example has empty lines.
        #       specifically, because confirmed_lines cannot continue Nones (for obj creation later),
        #       they need to be stripped out, and that ends up de-synchronizing line numbers
        #       in the example from indices in confirmed_lines.
        #       So I recommend avoiding having empty lines, though that is something that should
        #       for sure be tested eventually.
        test_lines : List[str] = [
        "`@Tufts 177 College Ave", # 0
        "Medford, MA 02155", # 1
        "# Tufts address", # 2
        "`@CheesecakeRes success", # 3
        "@Contributor Polina Shpilker", # TODO : make sure references can handle spaces # 4
        "@Contributor-Association Tufts University `@Tufts", # 5
        "@Contributor-Email polina.shpilker@tufts.edu", # 6
        "@Contributor-Notes Contemplating cheesecake recipes", # 7
        "The peanut butter cheesecake was a `@{CheesecakeRes}.", # 8
        "@Contributor-Notes No, I couldn't think of a better example.", # 9
        "# Here's where I'd put my multiline comment...", # 10
        "# ... if I had one!", # 11
        "@Contributor Kiki Shpilker", # 12
        "@Contributor-Association None", # 13
        " No, really. She's a cat.", # 14
        "@Contributor-Notes Is very upset over her lack of dry food." # 15
        ]

        test_Lines : List[Optional[Line]] = []
        for idx, l in enumerate(test_lines) :
            test_Lines.append(LineReader.process_line(l, idx))

        confirmed_lines : List[Line] = []
        for idx, L in enumerate(test_Lines) :
            assert L is not None
            confirmed_lines.append(L)

        lc : LineCollector = LineCollector(confirmed_lines)

        assert len(lc.named_blocks.keys()) == 1
        assert len(lc.defined_macros.keys()) == 2
        assert len(lc.comments) == 3

        assert 'Tufts' in lc.defined_macros.keys()
        assert 'CheesecakeRes' in lc.defined_macros.keys()
        assert 'Contributor' in lc.named_blocks.keys()
        assert len(lc.named_blocks['Contributor'].keys()) == 2
        assert 'Polina Shpilker' in lc.named_blocks['Contributor'].keys()
        assert 'Kiki Shpilker' in lc.named_blocks['Contributor'].keys()

        assert isinstance(confirmed_lines[0], MacroLine)
        assert isinstance(confirmed_lines[1], ContinueLine)
        assert isinstance(confirmed_lines[2], CommentLine)
        assert isinstance(confirmed_lines[3], MacroLine)
        assert isinstance(confirmed_lines[4], NovelDetailLine)
        assert isinstance(confirmed_lines[5], NovelDetailLine)
        assert isinstance(confirmed_lines[6], NovelDetailLine)
        assert isinstance(confirmed_lines[7], NovelDetailLine)
        assert isinstance(confirmed_lines[8], ContinueLine)
        assert isinstance(confirmed_lines[9], NovelDetailLine)
        assert isinstance(confirmed_lines[10], CommentLine)
        assert isinstance(confirmed_lines[11], CommentLine)
        assert isinstance(confirmed_lines[12], NovelDetailLine)
        assert isinstance(confirmed_lines[13], NovelDetailLine)
        assert isinstance(confirmed_lines[14], ContinueLine)
        assert isinstance(confirmed_lines[15], NovelDetailLine)

        macro1: Macro = Macro(confirmed_lines[0], [confirmed_lines[1]])
        macro2: Macro = Macro(confirmed_lines[3], None)

        detail_1 : List[Detail] = []
        detail_1.append(Detail(confirmed_lines[4]))
        detail_1.append(Detail(confirmed_lines[5]))
        detail_1.append(Detail(confirmed_lines[6]))
        detail_1.append(Detail(confirmed_lines[7], [confirmed_lines[8]]))
        detail_1.append(Detail(confirmed_lines[9]))

        detail_2 : List[Detail] = []
        detail_2.append(Detail(confirmed_lines[12]))
        detail_2.append(Detail(confirmed_lines[13], [confirmed_lines[14]]))
        detail_2.append(Detail(confirmed_lines[15]))

        block_1 = Block(detail_1)
        block_2 = Block(detail_2)

        comment_1 = confirmed_lines[2]
        comment_2 = confirmed_lines[10]
        comment_3 = confirmed_lines[11]

        assert lc.defined_macros['Tufts'] == macro1
        assert lc.defined_macros['CheesecakeRes'] == macro2

        assert lc.named_blocks['Contributor']['Polina Shpilker'] == block_1
        assert lc.named_blocks['Contributor']['Kiki Shpilker'] == block_2

        assert lc.comments == [comment_1, comment_2, comment_3]