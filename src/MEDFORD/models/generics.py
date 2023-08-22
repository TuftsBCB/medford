import datetime
from enum import Enum, Flag, auto
from MEDFORD.objs.linecollections import Block, Detail
from pydantic import BaseModel as PydanticBaseModel, field_validator
from pydantic import model_validator, computed_field
from typing import TypeVar, Tuple, List, Optional, Union

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
# TODO : I want to be able to use minorT instead of MinorsT; 
#       what in the dictionizer is making this not possible?
#       -> dictionizer can't know what's supposed to be singular and
#           what isn't, so is always returning lists...
#       -> Don't know how to work around that without having the
#           dictionizer know about the models.

# TODO: there's gotta be a better way to store & check MEDFORD versions.
all_versions = ["1.0","2.0"]

class BaseModel(PydanticBaseModel) :
    class Config:
        arbitrary_types_allowed = True
        #extra = 'allow' #comment out to check only defined attr

class BlockModel(BaseModel) :
    Block: Block

#############################################
# Helper Types                              #
#############################################

class RoleOpts(Flag) :
    HASROLES =  0 # TODO: does this actually only flag if they have a
                  #   role set, or does it also flag ones w/o roles?
    CORR = auto()
    FIRST = auto()
    OTHER = auto()
    # TODO: other types of Roles we'll want to recognize

#############################################
# Attributes                                #
#############################################

class MEDFORDmdl(BlockModel) :
    name: MinorT[str]
    Version: MinorsT[str] # TODO: a way to make this singular?

    @field_validator('Version')
    def check_version(cls, values) :
        # TODO: make this a more generic version checker, e.g. right
        #       regex format.
        if values == [] :
            raise ValueError("Need to define a custom error for missing data.")
        
        version_tuple = values[0]
        version = version_tuple[1]
        if version not in all_versions :
            raise ValueError(f"Version {version} not a valid Version number.")

        return values
    

class Journal(BlockModel):
    name: MinorT[str]
    #TODO: Validation? Do we care about proper format for this?
    Volume: OptMinorT[str]
    Issue: OptMinorT[str]
    Pages: OptMinorT[str]

class Date(BlockModel):
    name: Union[MinorT[datetime.date], MinorT[datetime.datetime]]
    Note: OptMinorT[str]
    
class Contributor(BlockModel) :
    name: MinorT[str]
    ORCID: OptMinorT[str] = None
    Association: OptMinorT[str] = None
    Role: OptMinorT[str] = None
    Email: OptMinorT[str] = None

    @model_validator(mode='after')
    def check_corresopnding_has_email(cls, v) :
        if v.Role is not None:
            roles = [r[1] for r in v.Role]
            if "Corresponding Author" in roles and v.Email is None:
                raise NotImplementedError("Need custom Missing Data Error type.")
        return v
    
    @computed_field
    @property
    def _role(self) -> RoleOpts :
        # TODO: this doesn't actually help the way I wanted it to.
        #       We want the LSP to be able to suggest values for the
        #       minor token, but there is no way for the LSP to see
        #       these strings. The flags are cool and all, but how
        #       can we expose the string equivalents to the LSP?
        cur_flags : RoleOpts = RoleOpts.HASROLES
        if self.Role is not None :
            roles = [r[1] for r in self.Role]
            if "Corresponding Author" in roles :
                cur_flags = cur_flags | RoleOpts.CORR
            if "First Author" in roles :
                cur_flags = cur_flags | RoleOpts.FIRST

        # proving to myself how flag enums work
        #if RoleOpts.FIRST & cur_flags :
        #    print("is first author")
        #if RoleOpts.CORR & cur_flags :
        #    print("is corresponding author")

        return cur_flags



#############################################
# File-Wide Validation                      #
#############################################

class Entity(BaseModel) :
    MEDFORD: MajorsT[MEDFORDmdl]
    Contributor: OptMajorT[Contributor]
