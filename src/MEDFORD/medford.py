from pathlib import PurePath
from pydantic import BaseModel, ValidationError
from MEDFORD.medford_detailparser import *
from MEDFORD.medford_detail import *
from MEDFORD.medford_models import BCODMO, Entity, StrDescModel
from MEDFORD.medford_BagIt import runBagitMode, BagIt
from MEDFORD.medford_error_mngr import *
import json

import argparse

from enum import Enum, auto


class MFDMode(Enum) :
    OTHER = 'OTHER'
    BCODMO = 'BCODMO'
    BAGIT = 'BAGIT'

    def __str__(self):
        return self.value

class ParserMode(Enum) :
    validate = 'validate'
    compile = 'compile'

    def __str__(self):
        return self.value

class ErrorMode(Enum) :
    first = 'FIRST'
    all = 'ALL'

    def __str__(self) :
        return self.value

class ErrorOrder(Enum) :
    type = 'TYPE'
    tokens = 'TOKENS'
    line = 'LINE'

    def __str__(self):
        return self.value


# Command Line Arguments
# TODO: How can I make it require an MFDMode value, but lowercase is OK?
#       Do I actually care?
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--mode", type=MFDMode, choices=list(MFDMode), default=MFDMode.OTHER, required=True,
    help="Which Output mode the MEDFORD parser should validate or compile for.")
parser.add_argument("action", type=ParserMode, choices=list(ParserMode),
    help="Whether the MEDFORD parser is only validating or actually compiling (performing any necessary adjustments or actions for the appropriate format, such as creating a Bag for the BagIt mode.)")
parser.add_argument("file", type=str, help="The input MEDFORD file to validate or compile.")
parser.add_argument("--write_json", action="store_true", default=False,
    help="Write a JSON file of the internal representation of the MEDFORD file beside the input MEDFORD file.")
parser.add_argument("--debug", "-d", "-v", action="store_true", default=False,
    help="Enable verbose mode for MEDFORD, enabling various debug messages during runtime.")
parser.add_argument("--error_mode", "-e", type=ErrorMode, choices=list(ErrorMode), default=ErrorMode.all,
    help="(ALL | FIRST) Whether to compile all errors or stop on the first error encountered.")
parser.add_argument("--error_sort", "-s", type=ErrorOrder, choices=list(ErrorOrder), default=ErrorOrder.line,
    help="(TYPE|TOKENS|LINE) How to sort the errors, if compiling all errors.")

def read_details(filename, err_mngr) :
    details = []
    with open(filename, 'r') as f:
        all_lines = f.readlines()
        dr = None
        for i, line in enumerate(all_lines):
            if(line.strip() != "") :
                # TODO: move the details collection logic to detail? I don't like that we have to pull the typing here.
                dr = detail.FromLine(line, i+1, dr, err_mngr)
                if isinstance(dr, detail_return) :
                    if dr.is_novel :
                        details.append(dr.detail)
    
    if err_mngr.has_major_parsing :
        return (True, details, err_mngr.return_syntax_errors())

    return (False, details, None)

def runMedford(filename, output_json, mode, error_mode, error_sort, action):
    class FieldError(Exception):
        pass

    detail._clear_cache()
    err_mngr = error_mngr(str(error_mode), str(error_sort))

    # TODO: add error catching for mis-formatting in here...
    # to test, change line 12 of pshpil_rnaseq.mfd to have a typo in the macro name.
    (has_err, details, errs) = read_details(filename, err_mngr)
    if has_err :
        err_mngr.print_syntax_errors()
        raise SystemExit(0)

    parser = detailparser(details, err_mngr)
    final_dict = parser.export()
    p = {}
    # nom
    try:
        if mode == MFDMode.BCODMO:
            p = BCODMO(**final_dict)
        elif mode == MFDMode.BAGIT:
            p = BagIt(**final_dict)
            if mode == MFDMode.BAGIT and action == ParserMode.compile:
                runBagitMode(p, filename)

        elif mode == MFDMode.OTHER:
            p = Entity(**final_dict)
        else :
            raise Exception("Medford is running in an unsupported mode.")
    except ValidationError as e:
        parser.parse_pydantic_errors(e, final_dict)
    else:
        print("No errors found.")

    if(output_json) :
        with open(filename.parent / (filename.name + ".JSON"), 'w') as f:
            json.dump(final_dict, f, indent=2)

def parse_args_and_go() :
    args = parser.parse_args()
    runMedford(PurePath(args.file), args.write_json, args.mode, args.error_mode, args.error_sort, args.action)

if __name__ == "__main__":
    parse_args_and_go()
