from typing import List, Dict
from MEDFORD.objs.linereader import LineReader, Line
from MEDFORD.objs.linecollector import LineCollector, Macro, Block
from MEDFORD.objs.dictionizer import Dictionizer
from MEDFORD.models.generics import Entity
# order of ops:
# 1. open file
# 2. turn all lines into Line objs (using LineReader)
# 3. turn Line objs into specialized objs (using LineCollector)
# 4. turn specialized objs into dict (using ?)
# 5. verify dict using Pydantic (using ?)

# TODO : add error mgmt

class MFD() :
    filename: str
    object_lines: List[Line]
    line_collector: LineCollector
    dictionizer: Dictionizer

    macro_definitions: Dict[str, Macro]
    named_blocks: Dict[str, Block]

    dict_data = None
    pydantic_version = None

    def __init__(self, filename) :
        self.filename = filename

    def runMedford(self):
        # TODO: way to avoid putting all lines into memory?
        # TODO: make LineProcessor take all of the strs/filename and do the work itself?
        # 1, 2
        self.object_lines = self._get_Line_objects(self.filename)

        # 3
        self.line_collector = self._get_Line_Collector(self.object_lines)
        # TODO : shouldn't have to reach into line collector.
        self.macro_definitions = self.line_collector.defined_macros
        self.named_blocks = self.line_collector.named_blocks
        self.blocks = [v for k,v in self.named_blocks.items()]

        # 4
        self.dictionizer = self._get_Dictionizer(self.macro_definitions)
        self.dict_data = self.dictionizer.generate_dict(self.blocks)

        # 5
        # TODO : this kind of breaks all of my type checking and requires
        # me to use Dict[str, Any] instead of Dict[str, Dict[...]]...
        # maybe in the future look into fixing this?
        #   problem is Blocks aren't Dicts.
        self.pydantic_version = Entity(**self.dict_data)

    def _get_Line_objects(self, filename: str) -> List[Line] :
        object_lines = []
        with open(filename, 'r') as f :
            for idx,line in enumerate(f.readlines()) :
                p_line = LineReader.process_line(line, idx)
                if p_line is not None :
                    object_lines.append(p_line)

        return object_lines

    def _get_Line_Collector(self, object_lines: List[Line]) -> LineCollector:
        return LineCollector(object_lines)

    def _get_Dictionizer(self, macro_definitions: Dict[str, Macro]) -> Dictionizer :
        return Dictionizer(macro_definitions)

