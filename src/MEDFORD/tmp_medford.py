from typing import List
from MEDFORD.objs.lines import Line
from MEDFORD.objs.linereader import LineReader
from MEDFORD.objs.linecollector import LineCollector
# order of ops:
# 1. open file
# 2. turn all lines into Line objs (using LineReader)
# 3. turn Line objs into specialized objs (using LineProcessor)
# 4. turn specialized objs into JSON (using ?)
# 5. verify JSON using Pydantic (using ?)

# TODO : add error mgmt

class MFD() :
    filename: str
    object_lines: List[Line]
    line_collector: LineCollector

    def __init__(self, filename) :
        self.filename = filename

    def runMedford(self):
        # TODO: way to avoid putting all lines into memory?
        # TODO: make LineProcessor take all of the strs/filename and do the work itself?
        # 1, 2
        self.object_lines = self._get_Line_objects(self.filename)

        # 3
        self.line_collector = self._get_Line_Collector(self.object_lines)

        # 4
        # TODO : self.line_processor.JSON?

        # 5
        # TODO : cat_scream.gif

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

