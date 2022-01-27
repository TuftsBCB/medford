from pydantic import ValidationError
from medford_detailparser import *
from medford_detail import *
from medford_models import BCODMO, Entity
from medford_BagIt import runBagitMode, BagIt
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

def runMedford(filename, output_json, mode):
    class FieldError(Exception):
        pass

    details = []
    with open(filename, 'r') as f:
        all_lines = f.readlines()
        dr = None
        for i, line in enumerate(all_lines):
            if(line.strip() != "") :
                # TODO: move the details collection logic to detail? I don't like that we have to pull the typing here.
                dr = detail.FromLine(line, i+1, dr)
                if isinstance(dr, detail_return) :
                    if dr.is_novel :
                        details.append(dr.detail)

    parser = detailparser(details)
    final_dict = parser.export()
    try:
        if mode == MFDMode.BCODMO:
            p = BCODMO(**final_dict)
        elif mode == MFDMode.BAGIT:
            p = BagIt(**final_dict)
            runBagitMode(p, filename)
        elif mode == MFDMode.OTHER:
            p = Entity(**final_dict)
        else :
            raise Exception("Medford is running in an unsupported mode.")
    except ValidationError as e:
        parser.parse_pydantic_errors(e, final_dict)

    if(output_json) :
        with open(filename + ".JSON", 'w') as f:
            json.dump(final_dict, f, indent=2)

def handle_errors(err, final_dict) :
    errors = err.errors()
    ### TODO:
    # 1. collapse all errors that happen at the same location
    # 2. figure out what the type was supposed to be, and human-ify-it
    # 2.5 figure out the specific combination of tokens that got us here -- technically can achieve this by crunching apart the error json. 
    #       May be worth moving this logic to the detailparser, since this will change with detailparser updates.
    # 3. save this as a new error message, accessing the info's loc to get the location in the file
    t_err = final_dict
    for key in errors[0]['loc'][:-1]:
        print(key)
        t_err = t_err[key]
    new_err = TypeError("ERROR: Provided @major-minor in line " + t_err[0] + " is of the wrong format. It needs to be TYPE, but instead is TYPE.")
    #errors[0]['loc']
    raise NotImplementedError()

if __name__ == "__main__":
    args = parser.parse_args()
    runMedford(args.file, args.write_json, args.mode)