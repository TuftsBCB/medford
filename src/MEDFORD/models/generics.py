from MEDFORD.objs.linecollections import Block, Detail
from pydantic import BaseModel as PydanticBaseModel
from typing import TypeVar, Tuple, List, Optional

#############################################
# Building Blocks                           #
#############################################

T = TypeVar('T')
DatumT = Tuple[Detail, T]
DataT = List[DatumT[T]]
OptDataT = Optional[DataT[T]]

class BaseModel(PydanticBaseModel) :
    class Config:
        arbitrary_types_allowed = True

class BlockModel(BaseModel) :
    Block: Block

#############################################
# Attributes                                #
#############################################

class Contributor(BlockModel) :
    name: DatumT[str]
    ORCID: OptDataT[int]
    Association: OptDataT[str]
    Role: OptDataT[str]
    Email: OptDataT[str]

#############################################
# File-Wide Validation                      #
#############################################

class Entity(BaseModel) :
    Contributor: OptDataT[Contributor]
