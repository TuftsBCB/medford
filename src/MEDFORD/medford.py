"""Module containing the MEDFORD parser, which can validate and compile MEDFORD metadata files."""

import sys
from typing import List, Dict

import argparse
import json

from enum import Enum
from pathlib import PurePath #?

from MEDFORD.objs.linereader import LineReader, Line
from MEDFORD.objs.linecollector import LineCollector, Macro, Block
from MEDFORD.objs.dictionizer import Dictionizer
from MEDFORD.models.generics import Entity

import MEDFORD.mfdglobals as mfdglobals

# order of ops:
# 1. open file
# 2. turn all lines into Line objs (using LineReader)
# 3. turn Line objs into specialized objs (using LineCollector)
# 4. turn specialized objs into dict (using ?)
# 5. verify dict using Pydantic (using ?)

# TODO : add error mgmt
class ParserMode(Enum) :
    """Enum storing the mode of operation of the MEDFORD parser."""
    VALIDATE = 'validate'
    COMPILE = 'compile'

    def __str__(self) :
        return self.value

class OutputMode(Enum):
    """Enum storing possible outout types of the MEDFORD parser."""
    OTHER = 'OTHER'
    BCODMO = 'BCODMO'
    RDF = 'RDF'
    BAGIT = 'BAGIT'
    # TODO : Make creating a bag a separate option?
    # Could want to make an output RDF file AND zip it.

    def __str__(self) :
        return self.value

    @classmethod
    def _missing_(cls, value: str):
        for member in cls :
            if member.name.lower() == value.lower() :
                return member
        return None


ap = argparse.ArgumentParser(prog="MEDFORD parser")
# basic arguments
ap.add_argument("--version", action="version", version='%(prog)s v2.0')
ap.add_argument("action", type=ParserMode, choices=list(ParserMode),
                help="Whether to run the MEDFORD parser in Validation or Compilation mode. (Compilation creates a novel output file.)")
ap.add_argument("file", type=str,
                help="Input MEDFORD file to validate or compile.")
ap.add_argument("-m", "--mode", type=OutputMode, choices=list(OutputMode), default=OutputMode.OTHER,
                help="The output mode of the MEDFORD parser; what format should be validated against or compiled to.")

# argument for base directory of files for BagIT
ap.add_argument("--dir", type=str,
                help="Base directory of files described in the given Medford file for BagIt compression.")
# argument for "permissible" mode
ap.add_argument("--permissible", action="store_true", default=False,
                help="Enables permissible mode for the MEDFORD parser. This disables a significant number of the parser's validation features. (not implemented)")

# debug arguments
# TODO: Implement
ap.add_argument("--write_json", action="store_true", default=False,
                help="FOR DEBUG: Write a JSON file of the internal representation of the MEDFORD file beside the input MEDFORD file.")
# TODO: Implement
ap.add_argument("-d", "--debug", action="store_true", default=False,
                help="FOR DEBUG: Enable DEBUG mode for MEDFORD, enabling a significant amount of intermediate stdout output. (currently unimplemented.)")

class MFD() :
    """Base class runner of the MEDFORD parser. Runs the entire validation/compilation pipeline from file input to output."""

    # TODO : ? is this the right way to implement this?
    @classmethod
    def get_version(cls) -> str :
        """Returns the current MEDFORD parser version."""
        return "2.0.0"


    mfdglobals.init()

    filename: str
    object_lines: List[Line]
    line_collector: LineCollector
    dictionizer: Dictionizer

    write_json: bool
    output_path: str

    macro_definitions: Dict[str, Macro]
    blocks: List[Block]
    named_blocks: Dict[str, Block]

    dict_data = None
    pydantic_version = None

    def __init__(self, filename, write_json:bool=False, output_path:str=".") :
        self.filename = filename
        self.write_json = write_json
        self.output_path = output_path

    def run_medford(self):
        """Main function that runs MEDFORD compilation from start to finish."""
        self.em_inst = mfdglobals.validator # this is just for debug purposes
        
        # TODO: way to avoid putting all lines into memory?
        # TODO: make LineProcessor take all of the strs/filename and do the work itself?
        # 1, 2
        self.object_lines = MFD._get_line_objects(self.filename)

        # 3
        self.line_collector = MFD._get_line_collector(self.object_lines)
        self.macro_definitions = self.line_collector.get_macros()
        self.blocks = self.line_collector.get_flat_blocks()
        self.named_blocks = self.line_collector.get_1lvl_blocks()

        # stop here and check for syntax errors
        if mfdglobals.mv.instance().has_syntax_err() :
            print(f"Syntax errors found! : {mfdglobals.mv.instance().n_syntax_errs()} errors")
            mfdglobals.mv.instance().print_syntax_errs()
            sys.exit(1)
            # TODO : enter error mode

        # 4
        self.dictionizer = MFD._get_dictionizer(self.macro_definitions, self.named_blocks)
        self.dict_data = self.dictionizer.generate_dict(self.blocks)

        if mfdglobals.mv.instance().has_other_err() :
            print(f"Other errors found! : {mfdglobals.mv.instance().n_other_errs()} errors")
            sys.exit(1)
            # TODO : enter error mode

        # 5
        # TODO : this kind of breaks all of my type checking and requires
        # me to use Dict[str, Any] instead of Dict[str, Dict[...]]...
        # maybe in the future look into fixing this?
        #   The problem is that Blocks aren't Dicts.
        self.pydantic_version = Entity(**self.dict_data)
        if mfdglobals.mv.instance().has_pydantic_err() :
            mfdglobals.mv.instance().print_pydantic_errs()
        
        #try:
        #    self.pydantic_version = Entity(**self.dict_data)
        #    print(self.pydantic_version.dict())
        #except ValidationError as e:
        #    if(len(e.errors()) != mfdglobals.mv.instance().n_pydantic_errs()) :
        #        print("ERROR: Validation errors are not all being accounted for by the validator.")
        #        raise Exception("Missing validation errors")
        #    else :
        #        if mfdglobals.mv.instance().has_pydantic_err() :
        #            mfdglobals.mv.instance().print_pydantic_errs()

        # TODO: export to json, bag
        # TODO: implement all of the old models

        if self.write_json :
            if self.output_path == "." :
                with open("medford_output.json", 'w', encoding="utf-8") as f:
                    json.dump(self.dict_data, f, indent=2)

    @classmethod
    def _get_line_objects(cls, filename: str) -> List[Line] :
        object_lines = []
        with open(filename, 'r', encoding="utf-8") as f :
            for idx,line in enumerate(f.readlines()) :
                p_line = LineReader.process_line(line, idx)
                if p_line is not None :
                    object_lines.append(p_line)

        return object_lines
    
    # for testing purposes in model unit tests
    @classmethod
    def _get_unvalidated_blocks(cls, input: str)-> List[Block] :
        object_lines = MFD._get_line_objects(input)
        line_collector = MFD._get_line_collector(object_lines)
        #macro_definitions = line_collector.get_macros()
        blocks = line_collector.get_flat_blocks()

        return blocks


    # note for later: what happens when it takes too long to process ?
    # user writes a new line, add it to LineCollector that single line at a time?
    # 10s of ms amount of time to run is allocation usually
    @classmethod
    def _get_line_collector(cls, object_lines: List[Line]) -> LineCollector:
        return LineCollector(object_lines)

    @classmethod
    def _get_dictionizer(cls, macro_definitions: Dict[str, Macro], name_dictionary: Dict[str, Block]) -> Dictionizer :
        return Dictionizer(macro_definitions, name_dictionary)


# wants to: ask parser what major/minor tokens it understands
# -> dumping schema of Entity & parsing manually

# syntax check -> get back both line objects & errors

# want full API call to include all minor api calls; return dict w/ string indices?
def parse_args_and_go() :
    args = ap.parse_args()
    mfd = MFD(PurePath(args.file))
    mfd.run_medford()

if __name__ == "__main__" :
    parse_args_and_go()
