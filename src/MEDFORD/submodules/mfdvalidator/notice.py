from abc import ABC, abstractmethod
from typing import List, Union
from enum import Enum, auto

class Notice(ABC) :
    name: str       # a name for the notice type, usually just str version of class name

    msg: str        # short message about error
    help_msg: str   # long form message that somehow includes actual content

    is_multiline: bool
    lines: List[int]

    def __init__(self, msg: str, help_msg: str, lines: Union[List[int], int]) :
        self.name = self.__class__.__name__ # Sets name to the name of the subclass

        self.msg = msg
        self.help_msg = help_msg

        if isinstance(lines, List) :
            self.is_multiline = (len(lines) > 1)
            self.lines = lines
        else :
            self.is_multiline = False
            self.lines = [lines]

    ### getter helper funcs ###

    def get_start_line(self) -> int :
        return self.lines[0]
    
    def get_end_line(self) -> int :
        return self.lines[-1]

    # TODO : deepcopy?
    def get_all_lines(self) -> List[int] :
        return self.lines

    ### abstract methods ###

    #@abstractmethod
    #def to_string() -> str :
    #    pass

############## WARNINGS ################################################

class MFDWarning(Notice) :
    def __init__(self, msg: str, help_msg: str, lines: Union[List[int], int]) :
        super().__init__(msg, help_msg, lines)

class UnknownWarning(MFDWarning) :
    # note: shouldn't really be used, but will be used as a filler until a more specific Warning is made.
    def __init__(self, lines: Union[List[int], int]) :
        msg: str = "Unknown warning encountered. Whatever this is, it won't break things, but it's uncomfortable."
        help_msg: str = "You've written something that the MFD parser thinks you shouldn't do, but we haven't figured out how to explain what you did. Whatever it is, you probably shouldn't do it! (But, it doesn't break anything, so go ahead if you really want to.)"

        super().__init__(msg, help_msg, lines)

class AtAtWarning(MFDWarning) :
    def __init__(self, lines: Union[List[int], int]) :
        msg: str = "AtAt is currently not supported."
        help_msg: str = "AtAt is currently being re-implemented; do not use the @Major-@Minor syntax as this will not be supported."

        super().__init__(msg, help_msg, lines)

################ ERRORS ################################################

class MFDError(Notice) :
    # possible categories of MFD error
    class Category(Enum) :
        OTHER = "other"                         # No idea how to categorize it
        SYNTAX = "syntax"                       # Incorrect syntax that prevents parsing, like no DESC line to name a block.
        PYDANTIC = "pydantic"                   # Pydantic threw an error.
        MISSING_CONTENT = "missing_content"     # Missing something required to correctly parse, but can still finish parsing
                                                #   (e.g. @-@ ref name, content in a line)
        MALFORMED_CONTENT = "malformed_content" # Content prevents post-intake parsing 
                                                #   (e.g. referenced block in @-@ does not exist)

    # possible severities of MFD error
    class Severity(Enum) :
        low = auto()    # finish parsing entire file
        med = auto()    # skip current block?
        high = auto()   # immediately stop parsing

    severity: Severity  # Errors have a severity, which informs the manager whether to immediately terminate parsing.
    category: Category  # the "type" of error, for grouping for display

    def __init__(self, msg:str, help_msg:str, lines: Union[List[int], int], severity:Severity, category:Category) :
        self.severity = severity

        super().__init__(msg, help_msg, lines)

class MissingDescError(MFDError) :
    # SPECIFICALLY, this means that a block is missing the DESC line
    #   (the NAME line), aka we don't have a name for the block.
    # IMO, this means don't even try to build the block. There's no
    #   point.
    major_token: str
    minor_token: str

    def __init__(self, detailobj) :
        category = MFDError.Category.SYNTAX
        severity = MFDError.Severity.high # maybe?

        from MEDFORD.objs.linecollections import Detail

        if not isinstance(detailobj, Detail) :
            raise ValueError("Attempted to create a MissingDescError without a Detail.")
        
        self.detail: Detail = detailobj
        self.major_token = "_".join(detailobj.major_tokens)
        if detailobj.minor_token is not None :
            self.minor_token = detailobj.minor_token
        else :
            raise ValueError("Attempted to create a MissingDescError when the detail has no minor token, aka is a desc line. (Which means the block isn't missing a desc line.)")

        msg: str = f"A new block for major token {self.major_token} was created without a Name line."
        help_msg: str = f"A MEDFORD Block should begin with a line like this:\n@{self.major_token} (name of this medford block)\n@{self.major_token}-{self.minor_token} %s" % (self.detail.get_raw_content())

        super().__init__(msg, help_msg, detailobj.get_linenos(), severity, category)