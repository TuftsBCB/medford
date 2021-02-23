from medford_models import *
from medford_smartdict import SmartDict
from functools import reduce 
from medford_token import Token
import json

#filename = "example_medford_files/pdam_cunning.MEDFORD"
filename = "example_medford_files/made_up_BCODMO.MEDFORD"
output_json = True
# Jack - work on how to turn JSON into other file format?
# Unrecognized token warning, not error
class FieldError(Exception):
    pass

tokens = Token.generate_tokens(filename)
output = SmartDict(Token.get_major_tokens(tokens))
blocks = Token.get_token_blocks(tokens)
verbose = False

for i, index in enumerate(blocks):
    curblock_tokens = tokens[index : blocks[i+1] if i < (len(blocks) - 1) else len(tokens)]
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
    output.add(tokens[index].get_major(), curdict.export())

final_dict = output.export()
p = BCODMO(**final_dict)
if(output_json) :
    with open(filename + "_JSON", 'w') as f:
        json.dump(final_dict, f)