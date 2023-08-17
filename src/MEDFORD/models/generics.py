from MEDFORD.objs.linecollections import Block, Detail
from pydantic import BaseModel as PydanticBaseModel, Extra
from typing import TypeVar, Tuple, List, Optional

#############################################
# Building Blocks                           #
#############################################

# need to compile this into a file the LSP can use
# should have it run as a git commit compile thingie to generate
# the file and then the LSP can pull from that.
#
# for now, updates to generics.py should be patch updates
# will figure out how to deal with this once people are adding their
# own major/minor tokens later.
T = TypeVar('T')
MinorT = Tuple[Detail, T]
MinorsT = List[MinorT[T]]
OptMinorT = Optional[MinorsT[T]]

MajorsT = List[T]
OptMajorT = Optional[MajorsT[T]]


class BaseModel(PydanticBaseModel) :
    class Config:
        arbitrary_types_allowed = True
        extra = 'allow'

class BlockModel(BaseModel) :
    Block: Block

#############################################
# Attributes                                #
#############################################

class Contributor(BlockModel) :
    name: MinorT[str]
    ORCID: OptMinorT[int]
    Association: OptMinorT[str]
    Role: OptMinorT[str]
    Email: OptMinorT[str]

#############################################
# File-Wide Validation                      #
#############################################

class Entity(BaseModel) :
    Contributor: OptMajorT[Contributor]
