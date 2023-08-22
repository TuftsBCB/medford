from typing import List, Dict

from pydantic import ValidationError
from MEDFORD.objs.linereader import LineReader, Line
from MEDFORD.objs.linecollector import LineCollector, Macro, Block
from MEDFORD.objs.dictionizer import Dictionizer
from MEDFORD.models.generics import Entity

from MEDFORD.submodules.medforderrors.errormanager import MedfordErrorManager as em

import argparse

from enum import Enum
from pathlib import PurePath #?

# order of ops:
# 1. open file
# 2. turn all lines into Line objs (using LineReader)
# 3. turn Line objs into specialized objs (using LineCollector)
# 4. turn specialized objs into dict (using ?)
# 5. verify dict using Pydantic (using ?)

# TODO : add error mgmt
class ParserMode(Enum) :
    validate = 'validate'
    compile = 'compile'

    def __str__(self) :
        return self.value

class OutputMode(Enum):
    OTHER = 'OTHER'
    BCODMO = 'BCODMO'
    RDF = 'RDF'
    BAGIT = 'BAGIT' 
    # TODO : Make creating a bag a separate option?
    # Could want to make an output RDF file AND zip it.

    def __str__(self) :
        return self.value
    
    @classmethod
    def _missing_(cls, name):
        for member in cls :
            if member.name.lower() == name.lower() :
                return member
    

ap = argparse.ArgumentParser()
# basic arguments
ap.add_argument("action", type=ParserMode, choices=list(ParserMode),
                help="Whether to run the MEDFORD parser in Validation or Compilation mode. (Compilation creates a novel output file.)")
ap.add_argument("file", type=str, 
                help="Input MEDFORD file to validate or compile.")
ap.add_argument("-m", "--mode", type=OutputMode, choices=list(OutputMode), default=OutputMode.OTHER,
                help="The output mode of the MEDFORD parser; what format should be validated against or compiled to.")

# debug arguments
# TODO: Implement
ap.add_argument("--write_json", action="store_true", default=False,
                help="FOR DEBUG: Write a JSON file of the internal representation of the MEDFORD file beside the input MEDFORD file.")
# TODO: Implement
ap.add_argument("-d", "--debug", action="store_true", default=False,
                help="FOR DEBUG: Enable DEBUG mode for MEDFORD, enabling a significant amount of intermediate stdout output. (currently unimplemented.)")

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
        self.macro_definitions = self.line_collector.get_macros()
        self.blocks = self.line_collector.get_flat_blocks()
        self.named_blocks = self.line_collector.get_1lvl_blocks()

        # 4
        self.dictionizer = self._get_Dictionizer(self.macro_definitions, self.named_blocks)
        self.dict_data = self.dictionizer.generate_dict(self.blocks)

        # 5
        # TODO : this kind of breaks all of my type checking and requires
        # me to use Dict[str, Any] instead of Dict[str, Dict[...]]...
        # maybe in the future look into fixing this?
        #   The problem is that Blocks aren't Dicts.
        try :
            self.pydantic_version = Entity(**self.dict_data)
            print(self.pydantic_version.dict())
        except ValidationError as e:
            em.instance().handle_pydantic_errors(e)

        # TODO: export to json, bag
        # TODO: implement all of the old models

    def _get_Line_objects(self, filename: str) -> List[Line] :
        object_lines = []
        with open(filename, 'r') as f :
            for idx,line in enumerate(f.readlines()) :
                p_line = LineReader.process_line(line, idx)
                if p_line is not None :
                    object_lines.append(p_line)

        return object_lines

    # note for later: what happens when it takes too long to process ?
    # user writes a new line, add it to LineCollector that single line at a time?
    # 10s of ms amount of time to run is allocation usually
    def _get_Line_Collector(self, object_lines: List[Line]) -> LineCollector:
        return LineCollector(object_lines)

    def _get_Dictionizer(self, macro_definitions: Dict[str, Macro], name_dictionary: Dict[str, Block]) -> Dictionizer :
        return Dictionizer(macro_definitions, name_dictionary)


# wants to: ask parser what major/minor tokens it understands
# -> dumping schema of Entity & parsing manually

# syntax check -> get back both line objects & errors

# want full API call to include all minor api calls; return dict w/ string indices?

if __name__ == "__main__" :
    args = ap.parse_args()
    #print(args.mode)
    mfd = MFD(PurePath(args.file))
    mfd.runMedford()