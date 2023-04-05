from MEDFORD.objs.detail import Detail
from typing import List, Optional

class Block :
    major_token: str
    minor_tokens: List[str]
    
    has_macros: bool = False
    used_macros: Optional[List[str]]
    name: str

    def __init__(self, details: List[Detail]) :
        if len(details) == 0 :
            raise ValueError("Attempted to create a block with no details.")
        
        # ?
        self.major_token = "_".join(details[0].major_tokens)
        if details[0].minor_token is not None and details[0].minor_token != "" :
            raise ValueError("No desc line for first detail provided to Block constructor.")
        self.name = details[0].raw_payload()

        if len(details) > 0 :
            for idx, detail in enumerate(details[1:]) :
                if "_".join(detail.major_tokens) != self.major_token :
                    raise ValueError("Block provided details of multiple major tokens: Block Major is %s while line %d has major of %s." % (self.major_token, idx, "_".join(detail.major_tokens)))
                if detail.minor_token is None :
                    raise ValueError("Block provided a detail with no minor token past first detail: detail # %d." % (idx))
                
                self.minor_tokens.append(detail.minor_token)

                if detail.has_macros and detail.macro_uses is not None :
                    if self.used_macros is None :
                        self.used_macros = []
                        self.has_macros = True

                    for macro_use in detail.macro_uses :
                        if macro_use not in self.used_macros :
                            self.used_macros.append(macro_use)

        return