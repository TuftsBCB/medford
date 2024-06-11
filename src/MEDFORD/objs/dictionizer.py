"""Module contains the Dictionizer class for managing "two-pass" features,
such as macro definitions and generating the output dictionary for pydantic
consumption."""

from typing import Any, List, Dict
from MEDFORD.objs.linecollections import Block, Macro

class Dictionizer() :
    """Class to handle dictionary-based management of MEDFORD metadata.
    Essentially, any features that require "two-pass" parsing are handled 
    via this class.
    
    Examples include generating a dictionary to store macro names and their
    content (stored in the variable macro_dictionary) and a function to
    generate a dictionary from a list of the completed Blocks."""
    macro_dictionary: Dict[str, Macro]
    resolved_macros: Dict[str, str]
    name_dictionary: Dict[str, Block]

    def __init__(self, macro_dictionary: Dict[str, Macro], name_dictionary: Dict[str, Block]) :
        self.macro_dictionary = macro_dictionary
        self.name_dictionary = name_dictionary
        self.resolved_macros = {}
        # TODO : separate into a different function, tbh
        # ask the macros to resolve themselves
        for (n,m) in macro_dictionary.items() :
            res = m.resolve(self.macro_dictionary)
            if not isinstance(res, str) :
                raise ValueError(f"Attempting to resolve macro {m.name} resulted in an error return, not a string.")
            self.resolved_macros[n] = res


    def validate_atat(self, bls: List[Block]) :
        """DEPRECIATED. Does nothing."""
        all_valid = True
        for bl in bls :
            all_valid = all_valid and bl.validate_atat(self.resolved_macros, self.name_dictionary)
        if not all_valid :
            print("There is an invalid @-@ somewhere.")
        else :
            print("All @-@ successfully validated")

    def generate_dict(self, bls: List[Block]):
        """Generate the proper form dictionary from a list of Blocks to pass 
        to Pydantic."""
        self.validate_atat(bls)
        root_dict: Dict[str, Any] = {}
        for _, bl in enumerate(bls) :
            self._recurse_majors(root_dict, bl)

        return root_dict

    def _recurse_majors(self, cur_parent_dict: Dict[str, List[Dict]], cur_block: Block, cur_major_ind: int = 0) :
        c_mt: str = cur_block.major_tokens[cur_major_ind]
        if c_mt not in cur_parent_dict :
            cur_parent_dict[c_mt] = []
        cur_parent_dict[c_mt].append({'Block': cur_block})

        if cur_major_ind == len(cur_block.major_tokens) - 1 :
            self._parse_minors(cur_parent_dict[c_mt][-1], cur_block)
        else :
            self._recurse_majors(cur_parent_dict[c_mt][-1], cur_block, cur_major_ind + 1)

    # TODO : dict structure is complicated, fix
    def _parse_minors(self,cur_parent_dict: Dict[str, Any], cur_block: Block) :
        # TODO : sometimes name is called from block, sometimes it's called from details...?
        # concerned about when Macros are actually parsed, can have a macro in a name?
        # saying no for now. add to validation for Blocks?
        cur_parent_dict["name"] = (cur_block.head_detail, cur_block.name)
        if cur_block.minor_tokens is not None :
            for _, (minor, detail) in enumerate(cur_block.minor_tokens) :
                if minor not in cur_parent_dict.keys() :
                    cur_parent_dict[minor] = []
                cur_parent_dict[minor].append((detail, detail.get_content(self.resolved_macros)))
