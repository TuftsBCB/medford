
from enum import Enum
from typing import List, Dict, Tuple, Optional
from MEDFORD.objs.lines import AtAtLine, Line, MacroLine, NovelDetailLine, ContinueLine, CommentLine
from MEDFORD.objs.linecollections import AtAt, Macro, Block, Detail

class LineCollector() :
    defined_macros: Dict[str, Macro]
    named_blocks: Dict[str, Dict[str, Block]]
    comments: List[CommentLine]
    # TODO: what if multiple blocks with the same name?
    #       ADJUSTED: 2 layer dict, first by block major then by name
    # TODO: provide error handler?

    # how do I actually make this usable? still have to type LineCollector.(name) to use any of these.
    class CollectorState(Enum) :
        NA = 0
        MACRO = 1
        DETAIL = 2
        COMMENT = 3
        ATAT = 4

    na = CollectorState.NA
    macro = CollectorState.MACRO
    detail = CollectorState.DETAIL
    comment = CollectorState.COMMENT
    atat = CollectorState.ATAT

    def __init__(self, lines: List[Line]) :
        self.defined_macros = {}
        self.named_blocks = {}
        self.comments = []

        self._ProcessLines(lines)
    
    def _ProcessLines(self, lines: List[Line]):
        state: str = "na" # ?
        line_collection = [] 
        # TODO : figure out how to add type to line_collection without everything exploding
        detail_collection: List[Detail] = []
            
        for line in lines :
            line_collection, detail_collection = self._check_do_completion(False, line, state, line_collection, detail_collection)

            if isinstance(line, MacroLine) :
                state = "macro"
                line_collection.append(line)
            
            elif isinstance(line, AtAtLine) :
                state = "atat"
                line_collection.append(line)

            elif isinstance(line, NovelDetailLine) :
                state = "detail"
                line_collection.append(line)
            
            elif isinstance(line, ContinueLine) :
                # TODO : ensure no continue lines after comments?
                line_collection.append(line)
            
            elif isinstance(line, CommentLine) :
                state = "comment"
                line_collection.append(line)

        # finish up
        if state != "na" :
            _,_ = self._check_do_completion(True, None, state, line_collection, detail_collection)
        else :
            raise ValueError("Somehow reached completion of _ProcessLines without changing state.")

    
    def _generate_blocks(self, detail_coll: List[Detail]) -> List[Block] :
        # iterate thru details and put them into blocks
        tmp_coll: List[Detail] = [detail_coll[0]]
        block_coll: List[Block] = []

        if len(detail_coll) > 1 :
            for idx, d in enumerate(detail_coll[1:]) :
                # TODO: ?
                if len(block_coll) > 0 :
                    if d.is_header or d.major_tokens != tmp_coll[0].major_tokens :
                        block_coll.append(Block(tmp_coll))
                        tmp_coll = [d]
                    else :
                        tmp_coll.append(d)
                else :
                    if d.is_header :
                        block_coll.append(Block(tmp_coll))
                        tmp_coll = [d]
                    else :
                        tmp_coll.append(d)
            
            block_coll.append(Block(tmp_coll))

        else :
            return [Block(tmp_coll)]

        return block_coll

    def _check_do_completion(self, final: bool, line:Optional[Line], state:str, line_collection, detail_collection: List[Detail]) -> Tuple[List[Line],List[Detail]] :
        if final or (state != "na" and not isinstance(line, ContinueLine)) :
            # finish whatever we're holding right now

            # should probably have a mixin shared between macro and detail
            #   to handle macro stuff
            if state == "macro" :
                headline = line_collection[0]
                extralines = None
                if len(line_collection) > 1 :
                    extralines = line_collection[1:]

                m = Macro(headline, extralines)
                self.defined_macros[m.name] = m

            elif state == "comment" :
                self.comments.extend(line_collection)
                # just throw the comment into the pile

            elif state == "detail" :
                headline = line_collection[0]
                extralines = None
                if len(line_collection) > 1 :
                    extralines = line_collection[1:]
                
                d = Detail(headline, extralines)
                detail_collection.append(d)

            elif state == "atat" :
                headline = line_collection[0]
                extralines = None
                if len(line_collection) > 1 :
                    extralines = line_collection[1:]
                a = AtAt(headline, extralines)
                detail_collection.append(a)

            line_collection = []

        if (final and (detail_collection is not None) and len(detail_collection) > 0) or \
                (state == "detail" and not (isinstance(line, NovelDetailLine) or isinstance(line, ContinueLine) or \
                                            isinstance(line, CommentLine))) :
            bs = self._generate_blocks(detail_collection)
            for b in bs :
                major = b.get_str_major()
                if major not in self.named_blocks.keys() :
                    self.named_blocks[major] = {}
                self.named_blocks[b.get_str_major()][b.name] = b

            detail_collection = []

        return (line_collection, detail_collection)

    def get_flat_blocks(self) -> List[Block] :
        t : List[Dict[str, Block]] = [named_blocks for major_token, named_blocks in self.named_blocks.items()]
        out : List[Block] = []
        for name_dict in t :
            out.extend([block for name, block in name_dict.items()])
        return out
    
    # combines major token with name to flatten 2-level dict into 1 level
    # later can be adjusted to keep 2 layer, but requires adjustment of Dictionizer
    def get_1lvl_blocks(self) -> Dict[str, Block] :
        tdict: Dict[str, Block] = {}
        for major in self.named_blocks.keys() :
            for name, block in self.named_blocks[major].items() :
                tdict[major + '@' + name] = block

        return tdict

    def get_macros(self) -> Dict[str, Macro] :
        return self.defined_macros