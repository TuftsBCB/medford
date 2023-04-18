from MEDFORD.objs.linecollections import Block, Detail
from typing import Any, List, Dict, Tuple, Union

class Dictionizer() :
    def __init__(self, macro_dictionary: Dict[str, str]) :
        self.macro_dictionary = macro_dictionary

    def generate_dict(self, bls: List[Block]) -> Dict[str, List[Dict]]:
        root_dict: Dict[str, List[Dict]] = {}
        for idx, bl in enumerate(bls) :
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
        cur_parent_dict["name"] = cur_block.name
        if cur_block.minor_tokens is not None :
            for idx, (minor, detail) in enumerate(cur_block.minor_tokens) :
                if minor not in cur_parent_dict.keys() :
                    cur_parent_dict[minor] = []
                cur_parent_dict[minor].append((detail, detail.get_content(self.macro_dictionary)))