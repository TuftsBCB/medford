from enum import Enum
from typing import List, Optional, Tuple

class ErrType(Enum) :
    OTHER = "other"
    SYNTAX = "syntax"
    PYDANTIC = "pydantic"
    MISSING_CONTENT = "missing_content"
    MALFORMED_CONTENT = "malformed_content"

class MFDErr():
    #lineobjs: List[Line]
    errname: str
    errtype: ErrType
    msg: str # verbose-ish error message
    helpmsg: str # extended error message for user help

    def __init__(self, errname: str, msg: str, helpmsg: str) :
        #self.lineobjs = lineobjs
        self.errname = errname
        self.msg = msg
        self.helpmsg = helpmsg
        # TODO: implement

    def get_head_lineno(self) -> int :
        raise NotImplementedError("not implemented :)")
    
    def get_lineno_range(self) -> Tuple[int, int] :
        raise NotImplementedError("also not implemented. :)")
    
    def _overwrite_msg(self, msg:str) -> None :
        self.msg = msg
    
    def _overwrite_helpmsg(self, helpmsg:str) -> None :
        self.helpmsg = helpmsg

# Syntax -> easy for discovery; helpful; fast
# Other -> other errors
# when possible, add specific character ranges of error

# Specific Error Types: Syntax
class MissingDescError(MFDErr) :
    # SPECIFICALLY, this means that a block is missing the DESC line
    #   (the NAME line), aka we don't have a name for the block.
    # IMO, this means don't even try to build the block. There's no
    #   point.
    major_token: str
    minor_token: str

    lineno_head: int
    lineno_range: Tuple[int, int]
    lineno_all: List[int]

    def __init__(self, detailobj) :
        self.errtype = ErrType.SYNTAX

        from MEDFORD.objs.linecollections import Detail

        if not isinstance(detailobj, Detail) :
            raise ValueError("Attempted to create a MissingDescError without a Detail.")
        
        self.detail: Detail = detailobj
        self.major_token = "_".join(detailobj.major_tokens)
        if detailobj.minor_token is not None :
            self.minor_token = detailobj.minor_token
        else :
            raise ValueError("Attempted to create a MissingDescError when the detail has no minor token, aka is a desc line.")

        self.lineno_all = detailobj.get_linenos()
        self.lineno_range = (min(self.lineno_all), max(self.lineno_all))
        self.lineno_head = self.lineno_range[0]

        message: str = f"A new block for major token {self.major_token} was created at line {self.lineno_head} without a Name line."
        helpmsg: str = f"A MEDFORD Block should begin with a line like this:\n@{self.major_token} (name of this medford block)\n@{self.major_token}-{self.minor_token} %s" % (self.detail.get_raw_content())

        super(MissingDescError, self).__init__(type(self).__name__, message, helpmsg)

    def get_head_lineno(self) -> int:
        return self.lineno_head
    
    def get_lineno_range(self) -> Tuple[int]:
        raise NotImplementedError("ahh")

class MissingContent(MFDErr) :
    major_token: str
    minor_token: str
    
    lineno_all: List[int]
    lineno_head: int
    lineno_range: Tuple[int, int]

    def __init__(self, detailobj) :
        self.errtype = ErrType.MISSING_CONTENT

        from MEDFORD.objs.linecollections import Detail
        
        if not isinstance(detailobj, Detail) :
            raise ValueError("Attempted to create a MissingContentError without a Detail.")
        
        self.detail : Detail = detailobj
        self.major_token = "_".join(detailobj.major_tokens)
        if detailobj.minor_token is not None :
            self.minor_token = detailobj.minor_token
        else :
            self.minor_token = "desc"

        self.lineno_all = detailobj.get_linenos()
        self.lineno_range = (min(self.lineno_all), max(self.lineno_all))
        self.lineno_head = self.lineno_range[0]

        message: str = f"A detail line on line {self.lineno_head} was created without any content: {self.major_token}"
        if self.minor_token != "desc" :
            message = message + f"-{self.minor_token}."
        helpmsg: str = f"All MEDFORD blocks must consist of either two or three parts: a name line, with a major token and content, or a detail line, with a major token, a minor token, and content."
        
        super(MissingContent, self).__init__(type(self).__name__, message, helpmsg)

    def get_head_lineno(self) -> int:
        return self.lineno_head
    
    def get_lineno_range(self) -> Tuple[int, int]:
        return self.lineno_range


# Specific Error Types: Other
class MaxMacroDepthExceeded(MFDErr) :
    lineno_all_flat: List[int] # list of ALL involved line no's
    lineno_all_2d: List[List[int]] # list of all involved line no's, split by macro
    lineno_head_each_macro: List[int] # list of only head line of each macro

    def __init__(self, macroobjs: List) :
        self.errtype = ErrType.OTHER

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

# Specific error types: Content


class MissingRequiredField(MFDErr) :
    major_token: str
    minor_token: str

    name: str

    lineno_head: int
    lineno_range: Tuple[int, int]
    lineno_all: List[int]

    def __init__(self, block_inp, missing_token:str) :
        self.errtype = ErrType.PYDANTIC

        from MEDFORD.objs.linecollections import Block
        
        if not isinstance(block_inp, Block) :
            raise ValueError("Attempted to create a MissingRequiredFieldError without a Block.")
        
        block_typed : Block = block_inp
        self.block : Block = block_typed

        self.major_token = block_typed.get_str_major()
        self.minor_token = missing_token
        self.name = block_typed.name

        message: str = f"Block for major token {self.major_token} named {self.name} is missing the required field {self.minor_token}."
        helpmsg: str = f"Blocks of major token {self.major_token} require a minor token of name {self.minor_token}, which can be written as:\n@{self.major_token}-{self.minor_token} CONTENT"

        super(MissingRequiredField, self).__init__(type(self).__name__, message, helpmsg)

    def get_head_lineno(self) -> int:
        if self.block is not None :
            return self.block.get_linenos()[0]
        else :
            raise ValueError("Attempted to get a head lineno of a {self.__name__} error that does not have a Block.")

    def get_lineno_range(self) -> Tuple[int, int]:
        if self.block is not None :
            temp_lines: List[int] = self.block.get_linenos()
            return (temp_lines[0], temp_lines[-1])
        else :
            raise ValueError("Attempted to get a lineno range of a {self.__name__} error that does not have a Block.")
    pass

class MissingRequiredFieldbcofLogic(MissingRequiredField) :
    def __init__(self, block_inp, missing_token:str, token_logic_str:str) :
        super(MissingRequiredFieldbcofLogic, self).__init__(block_inp, missing_token)

        message: str = f"Block for major token {self.major_token} named {self.name} is missing the required field {self.minor_token}, because {token_logic_str}."
        helpmsg: str = f"Blocks of major token {self.major_token} require a minor token of name {self.minor_token} when {token_logic_str}, which can be written as:\n@{self.major_token}-{self.minor_token} CONTENT"
        
        self._overwrite_msg(message)
        self._overwrite_helpmsg(helpmsg)

class InvalidValue(MFDErr) :
    major_token: str
    minor_token: str
    content: str

    name: str

    lineno_head: int
    lineno_range: Tuple[int, int]
    lineno_all: List[int]

    def __init__(self, block_inp, incorrect_token:str, content:str) :
        self.errtype = ErrType.PYDANTIC

        from MEDFORD.objs.linecollections import Block
        
        if not isinstance(block_inp, Block) :
            raise ValueError("Attempted to create an InvalidValue error without a Block.")
        
        block_typed : Block = block_inp
        self.block : Block = block_typed

        self.major_token = block_typed.get_str_major()
        self.minor_token = incorrect_token
        self.name = block_typed.name
        self.content = content

        message: str = f"Block for major token {self.major_token} named {self.name} has an invalid value for the minor token {self.minor_token} : {self.content}"
        helpmsg: str = message
        #TODO: make helpmsg more useful than msg

        super(InvalidValue, self).__init__(type(self).__name__, message, helpmsg)
    def get_head_lineno(self) -> int:
        if self.block is not None :
            return self.block.get_linenos()[0]
        else :
            raise ValueError("Attempted to get a head lineno of a {self.__name__} error that does not have a Block.")

    def get_lineno_range(self) -> Tuple[int, int]:
        if self.block is not None :
            temp_lines: List[int] = self.block.get_linenos()
            return (temp_lines[0], temp_lines[-1])
        else :
            raise ValueError("Attempted to get a lineno range of a {self.__name__} error that does not have a Block.")
    pass


class MissingAtAtName(MFDErr) :
    major_token: str
    referenced_major: str

    lineno_head: int
    lineno_range: Tuple[int, int]

    def __init__(self, major_token: str, referenced_major: str, lineno: int) :
        self.errtype = ErrType.MISSING_CONTENT

        self.major_token = major_token
        self.referenced_major = referenced_major
        self.lineno_head = lineno
        self.lineno_range = (lineno, lineno)
        # TODO: add msg, helpmsg, super call

    def get_head_lineno(self) -> int:
        return self.lineno_head
    
    def get_lineno_range(self) -> Tuple[int, int]:
        return self.lineno_range


class AtAtReferencedDoesNotExist(MFDErr) :
    major_token: str
    referenced_major: str
    referenced_name: str

    named_blocks: List[str]

    lineno_head : int
    lineno_range: Tuple[int, int]
    lineno_all: List[int]

    # TODO: add Blcok to give lineno range of block?
    def __init__(self, atat_inp, referenced_name: str, named_blocks: List[str]) :
        self.errtype = ErrType.MALFORMED_CONTENT

        from MEDFORD.objs.linecollections import AtAt
        
        if not isinstance(atat_inp, AtAt) :
            raise ValueError("Attempted to create an AtAtReferencedDoesNotExist without a Detail.")
        
        atat_typed : AtAt = atat_inp
        self.atat : AtAt = atat_typed

        self.major_token = atat_typed.get_str_majors()
        self.referenced_major = atat_typed.get_referenced_str_majors()
        self.referenced_name = referenced_name
        self.named_blocks = named_blocks

        message : str = f"Found an @-@ reference in a {self.major_token} that points to a {self.referenced_major} Block named {self.referenced_name} that does not exist."
        helpmsg : str = f"For this @-@ reference to work, there must exist a @{self.referenced_major} Block that starts with the line '@{self.referenced_major} {self.referenced_name}'."

        super(AtAtReferencedDoesNotExist, self).__init__(type(self).__name__, message, helpmsg)
    
    def get_head_lineno(self) -> int:
        if self.atat is not None :
            return self.atat.get_linenos()[0]
        else :
            raise ValueError("Attempted to get a head lineno of a {self.__name__} error that does not have an atat object.")
        

    def get_lineno_range(self) -> Tuple[int,int]:
        if self.atat is not None :
            temp_lines: List[int] = self.atat.get_linenos()
            return (temp_lines[0], temp_lines[-1])
        else :
            raise ValueError("Attempted to get a head lineno of a {self.__name__} error that does not have an atat object.")
        