from typing import List, Tuple


class MFDErr():
    #lineobjs: List[Line]
    errtype: str # TODO: not str?
    msg: str # verbose-ish error message
    helpmsg: str # extended error message for user help

    def __init__(self, errtype: str, msg: str, helpmsg: str) :
        #self.lineobjs = lineobjs
        self.errtype = errtype
        self.msg = msg
        self.helpmsg = helpmsg
        # TODO: implement

    def get_head_lineno(self) -> int :
        raise NotImplementedError("not implemented :)")
    
    def get_lineno_range(self) -> Tuple[int] :
        raise NotImplementedError("also not implemented. :)")

# Syntax -> easy for discovery; helpful; fast
# Other -> other errors
# when possible, add specific character ranges of error

# Specific Error Types: Syntax
class MissingDescError(MFDErr) :
    major_token: str
    minor_token: str

    lineno_head: int
    lineno_range: Tuple[int, int]
    lineno_all: List[int]

    def __init__(self, detailobj) :
        from MEDFORD.objs.linecollections import Detail

        if not isinstance(detailobj, Detail) :
            raise ValueError("Attempted to create a MissingDescError without a Detail.")
        
        self.detail: Detail = detailobj
        self.major_token = "_".join(detailobj.major_tokens)
        self.minor_found = detailobj.minor_token

        self.lineno_all = detailobj.get_linenos()
        self.lineno_range = (min(self.lineno_all), max(self.lineno_all))
        self.lineno_head = self.lineno_range[0]

        message: str = f"A new block for major token {self.major_token} was created at line {self.lineno_head} without a Name line."
        helpmsg: str = f"A MEDFORD Block should begin with a line like this:\n@{self.major_token} (name of this medford block)\n@{self.major_token}-{self.minor_found} %s" % (self.detail.get_raw_content())

        super(MissingDescError, self).__init__(type(self).__name__, message, helpmsg)

    def get_head_lineno(self) -> int:
        return self.lineno_head
    
    def get_lineno_range(self) -> Tuple[int]:
        raise NotImplementedError("ahh")

# Specific Error Types: Other
class MaxMacroDepthExceeded(MFDErr) :
    lineno_all_flat: List[int] # list of ALL involved line no's
    lineno_all_2d: List[List[int]] # list of all involved line no's, split by macro
    lineno_head_each_macro: List[int] # list of only head line of each macro

    def __init__(self, macroobjs: List) :
        from MEDFORD.objs.linecollections import Macro

        for (idx, mo) in enumerate(macroobjs) :
            if not isinstance(mo, Macro) :
                raise ValueError("{idx} entry in List passed to MaxMacroDepthExceeded is not a Macro.")
            
        macroobjs_typed: List[Macro] = macroobjs

        self.macros : List[Macro] = macroobjs_typed

        self.lineno_all_2d = []
        self.lineno_all_flat = []
        self.lineno_head_each_macro = []
        for (idx, mo) in enumerate(macroobjs_typed) :
            lns = mo.get_linenos()
            self.lineno_all_2d.append(lns)
            self.lineno_all_flat.extend(lns)
            self.lineno_head_each_macro.append(lns[0])
        
        message: str = f"Macro {self.macros[0].name} on line {self.lineno_head_each_macro[0]} is 11 references deep in a macro reference chain. (Macro history: %s)" % '->'.join([m.name for m in self.macros])
        helpmsg: str = "You can use a macro within a macro only up to 10 macros deep. You may have an loop of references (e.g. macro 1 uses macro 2, but macro 2 uses macro 1), or you need to reduce the number of layers. The full text of your macro reference is below: \n"
        for i in range(0, len(self.macros)) :
            helpmsg = helpmsg + "Lines (%d-%d): (%s) %s\n" % (self.lineno_all_2d[i][0], self.lineno_all_2d[i][-1], self.macros[i].name, self.macros[i].get_raw_content())

        super(MaxMacroDepthExceeded, self).__init__(type(self).__name__, message, helpmsg)

    def get_head_lineno(self) -> int:
        return self.lineno_head_each_macro[0]
    
    def get_lineno_range(self) -> Tuple[int]:
        raise NotImplementedError("ahh")