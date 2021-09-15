import os
import shutil
from medford_detailparser import *
from medford_detail import *
from medford_models import BCODMO, Entity
from functools import reduce 
from helpers_file import swap_file_loc
from medford_BagIt import runBagitMode, BagIt
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
        prev_detail = None
        for i, line in enumerate(all_lines):
            if(line.strip() != "") :
                noncomment, new_detail, returned_detail = detail.FromLine(line, i+1, prev_detail = prev_detail)
                if noncomment and new_detail :
                    details.append(returned_detail)
                if noncomment:
                    prev_detail = details[-1]

    parser = detailparser(details)
    final_dict = parser.export()
    parser.write("tmp.txt")
    if mode == MFDMode.BCODMO:
        p = BCODMO(**final_dict)
    elif mode == MFDMode.BAGIT:
        p = BagIt(**final_dict)
        # Iterate through all Files and:
        #   - create hash
        #   - copy to new subdir & location in data/
        runBagitMode(p, filename)
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
    #filename = "samples/made_up_Freeform.MFD"
    #filename = "samples/Shpilker_2021.mfd"
    filename = "samples/bagit_example/made_up_BAGIT.MFD"
    output_json = True

    runMedford(filename, output_json, MFDMode.BAGIT)