from medford_detailparser import *
from medford_detail import *
from medford_models import BCODMO, Entity, BagIt
from functools import reduce 
from helpers_file import swap_file_loc
import json

from enum import Enum

class MFDMode(Enum) :
    OTHER = 1
    BCODMO = 2
    BAGIT = 3

def runMedford(filename, output_json, mode):
    class FieldError(Exception):
        pass

    details = []
    with open(filename, 'r') as f:
        all_lines = f.readlines()
        for i, line in enumerate(all_lines):
            # TODO: Add logic for catching multi-line details...
            if(line.strip() != "" and line[0] == '@') :
                details.append(detail.FromLine(line, i))

    parser = detailparser(details)
    final_dict = parser.export()

    if mode == MFDMode.BCODMO:
        p = BCODMO(**final_dict)
    elif mode == MFDMode.BAGIT:
        p = BagIt(**final_dict)
    elif mode == MFDMode.OTHER:
        p = Entity(**final_dict)
    else :
        raise Exception("Medford is running in an unsupported mode.")

    if(output_json) :
        with open(filename + ".JSON", 'w') as f:
            json.dump(final_dict, f, indent=2)

if __name__ == "__main__":
    #filename = "samples/pdam_cunning.MFD"
    #filename = "samples/made_up_BCODMO.MFD"
    filename = "samples/made_up_Freeform.MFD"
    #filename = "samples/made_up_BAGIT.MFD"
    output_json = True

    runMedford(filename, output_json, MFDMode.OTHER)