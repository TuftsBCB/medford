from medford_detailparser import *
from medford_detail import *
from medford_models import BCODMO, Entity, BagIt
from functools import reduce 
from helpers_file import swap_file_loc
import json

MODE = "OTHER"
#MODE = "BAGIT"
#filename = "samples/pdam_cunning.MEDFORD"
#filename = "samples/made_up_BCODMO.MEDFORD"
filename = "samples/made_up_Freeform.MEDFORD"
#filename = "samples/made_up_BAGIT.MEDFORD"
output_json = True
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

#p = Entity(**final_dict)

if(output_json) :
    with open(filename + "_JSON", 'w') as f:
        json.dump(final_dict, f, indent=2)