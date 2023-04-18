from MEDFORD.objs.linecollections import Block, Detail
from pydantic import BaseModel as PydanticBaseModel
from typing import TypeVar, Tuple, List, Optional

#############################################
# Building Blocks                           #
#############################################

T = TypeVar('T')
MinorT = Tuple[Detail, T]
MinorsT = List[MinorT[T]]
OptMinorT = Optional[MinorsT[T]]

MajorsT = List[T]
OptMajorT = Optional[MajorsT[T]]


class BaseModel(PydanticBaseModel) :
    class Config:
        arbitrary_types_allowed = True

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
