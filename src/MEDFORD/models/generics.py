"""Module containing generic Model information for standard MEDFORD use. 
These are models that are expected to be used across multiple MEDFORD metadata applications, 
as well as some that are expected for our initial use case tests.

These Models are defined for use with Pydantic, and contain custom data types and type validation."""

import datetime
from enum import Flag, auto
from typing import TypeVar, Tuple, List, Optional, Union
from pydantic import BaseModel as PydanticBaseModel, field_validator
from pydantic import model_validator, computed_field
from MEDFORD.objs.linecollections import Block, Detail

from MEDFORD.submodules.mfdvalidator.validator import MedfordValidator as mv
from MEDFORD.submodules.mfdvalidator.errors import InvalidValue, MissingRequiredFieldbcofLogic
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
all_versions = ["1.0","1.1","2.0"]

class BaseModel(PydanticBaseModel) :
    """Base model for use by other MEDFORD model. Importantly, allows custom typing
    and additional attributes, allowing users to add arbitrary minor tokens."""
    class Config:
        """Configuration for the BaseModel allowing custom typing and extra attributes."""
        arbitrary_types_allowed = True
        extra = 'allow' #comment out to check only defined attr

class BlockModel(BaseModel) :
    """An extension to the BaseModel that adds an expected attribute Block,
    for cases where the Block information is being provided alongside the expected
    Model features."""
    Block: Block

#############################################
# Helper Types                              #
#############################################

class RoleOpts(Flag) :
    """A Flag describing author role features, such as Corresponding author or First author."""
    HASROLES =  0 # TODO: does this actually only flag if they have a role set, or does it also flag ones w/o roles?
    CORR = auto()
    FIRST = auto()
    OTHER = auto()
    # TODO: other types of Roles we'll want to recognize

#############################################
# Attributes                                #
#############################################

class MEDFORDmdl(BlockModel) :
    """Model to store MEDFORD metadata describing the MEDFORD file itself,
     such as MEDFORD file colloqiual name and the version of MEDFORD used
     to write this file."""
    name: MinorT[str]
    Version: MinorsT[str] # TODO: a way to make this singular?

    @model_validator(mode='after')
    @classmethod
    def check_version(cls, values) :
        """Ensures that the version described in this entry is a valid MEDFORD version."""
        # TODO: make this a more generic version checker, e.g. right
        #       regex format.
        if values.Version == [] :
            raise ValueError("Need to define a custom error for missing data.")
        
        version_tuple = values.Version[0]
        version = version_tuple[1]
        if version not in all_versions :
            mv.instance().add_error(InvalidValue(values.Block, 'Version', version))
#            raise ValueError(f"Version {version} not a valid Version number.")

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
    @classmethod
    def check_corresponding_has_email(cls, v) :
        if v.Role is not None:
            roles = [r[1] for r in v.Role]
            if "Corresponding Author" in roles and v.Email is None:
                mv.instance().add_error(MissingRequiredFieldbcofLogic(v.Block, "Email", "Corresponding Author is listed under Roles"))
                a = mv.instance()
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

        # pylint: disable=unsupported-binary-operation
        # known issue in pylint for py<3.11; throws false error when ENUMs are logic chained.
        # https://github.com/pylint-dev/pylint/issues/7381
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

class Funding(BlockModel):
    ID: OptMinorT[str]
    # TODO: research possible funding IDs so we can implement validation

class Keyword(BlockModel):
    pass



#############################################
# File-Wide Validation                      #
#############################################

class Entity(BaseModel) :
    MEDFORD: MajorsT[MEDFORDmdl]
    Contributor: OptMajorT[Contributor]
