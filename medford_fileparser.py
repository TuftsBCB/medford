from src.medford_models import BCODMO, Entity, BagIt
from src.medford_smartdict import SmartDict
from functools import reduce 
from src.medford_token import Token, TokenBlock
from src.output_compatibility.file_helpers import swap_file_loc
import json

MODE = "OTHER"
#MODE = "BAGIT"
filename = "samples/pdam_cunning.MEDFORD"
#filename = "samples/made_up_BCODMO.MEDFORD"
#filename = "samples/made_up_BAGIT.MEDFORD"
output_json = True
# Jack - work on how to turn JSON into other file format?
# Unrecognized token warning, not error
class FieldError(Exception):
    pass

tokens = Token.generate_tokens(filename)
blocks = []
for i, token in enumerate(tokens):
    if i == 0 :
        blocks = [TokenBlock(token)]
    else :
        if blocks[-1].same_block(token) :
            blocks[-1].add_token(token)
        else :
            blocks.append(TokenBlock(token))

output = SmartDict([x.get_major() for x in blocks])
verbose = True

for i, block in enumerate(blocks):
    curblock_tokens = block.get_iterable()
    if verbose: 
        print("****** RAW TOKENS ******")
        for token in curblock_tokens :
            print(token)
    revealed = Token.reveal_several(curblock_tokens)
    
    if verbose:
        print("******* REVEALED ********")
        for token in revealed:
            print(token)
    curdict = SmartDict(Token.get_major_tokens(revealed))
    
    if verbose:
        print("******* MAJOR TOKENS ********")
        print(Token.get_major_tokens(revealed))
    for token in revealed :
        curdict.addFromToken(token)
    
    if verbose:
        print("******* DICTIONARY ********")
        print(curdict.export())
    output.add(block.get_major(), curdict.export())

final_dict = output.export()
#p = BCODMO(**final_dict)
p = Entity(**final_dict)
#p = BagIt(**final_dict)
if(output_json) :
    with open(filename + "_JSON", 'w') as f:
        json.dump(final_dict, f, indent=2)

# TODO: Better output mode catching rofl
if MODE == "BAGIT" :
    # Change all file paths to be relative to the bag, so as to not reveal
    #   the user's directory structure when the bag is handed to other people.
    for i,f in enumerate(p.File) :
        p.File[i] = swap_file_loc(f)

print(p.File)