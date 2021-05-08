from pydantic import BaseModel, AnyUrl, validator
from typing import List, Optional, Union, Iterable
import datetime
from enum import Enum
from helpers_file import *

# bcodmo? + bag
# export to rtf?
# error on unknown fields
# data1 compliance ('dublin core'?)

# Validation of user-defined fields: in the future?
#       runtime clas creation?
#       parser level validation?

# Test against all data types;
#       Return which ones *can* submit to & which *cannot*
#       Can then re-run on specific mode to see specific errors

################################
# Helper Models                #
################################
class StrDescModel(BaseModel):
    desc: List[str] #TODO: Find a way to make an exception?
    Note: Optional[List[str]]

################################
# Field Models                 #
################################
class Paper(StrDescModel):
    Link: Optional[List[AnyUrl]]
    PMID: Optional[List[int]]
    #Add a validator for PMID?
    DOI: Optional[List[datetime.date]]

class Journal(StrDescModel):
    Volume: List[int]
    Issue: List[int]
    Pages: Optional[List[str]] #TODO: Validation?

class Date(BaseModel):
    desc: Union[List[datetime.date], List[datetime.datetime]]
    Note: List[str]
    #changed type to note because type is a reserved keyword

class Contributor(StrDescModel) :
    ORCID: Optional[List[int]]
    Assocation: Optional[List[str]]
    Role: Optional[List[str]]
    Email: Optional[List[str]] #TODO: Email validation

class Funding(StrDescModel) :
    ID: Optional[List[str]] #TODO: Funding ID validation?

class Keyword(StrDescModel):
    pass

class Species(StrDescModel):
    Loc: List[str]
    ReefCollection: List[str] # TODO: Change to date with note?
    Cultured: List[str]
    CultureCollection: List[str]

class Method(StrDescModel):
    Type: List[str]
    Company: Optional[List[str]]
    Sample: Optional[List[str]]

class Software(StrDescModel) :
    Type: List[str]
    Version: Optional[List[str]]

class DataTypeEnum(str, Enum):
    # TODO : How do we avoid caring about capitalization, tho?
    recorded = "recorded"
    referenced = "referenced"

class Data(StrDescModel) :
    Type: List[str]
    URI: Optional[List[AnyUrl]]
    Flag: List[DataTypeEnum] = [DataTypeEnum.referenced]

class Project(StrDescModel):
    pass

class Expedition(StrDescModel):
    ShipName: Optional[List[str]]
    CruiseID: Optional[List[str]]
    MooringID: Optional[List[str]]
    DiveNumber: Optional[List[int]]
    Synonyms: Optional[List[str]]

class ArbitraryFile(StrDescModel):
    Path: List[str]
    Subdirectory: Optional[List[str]]
    NewName: Optional[str]

################################
# Overarching Model            #
################################
# Meant to store every single possible tag that we have defined
class Entity(BaseModel):
    Paper: Optional[List[Paper]]
    Journal: Optional[List[Journal]]
    Date: Optional[List[Date]]
    Contributor: Optional[List[Contributor]]
    Funding: Optional[List[Funding]]
    Keyword: Optional[List[Keyword]]
    Species: Optional[List[Species]]
    Method: Optional[List[Method]]
    Software: Optional[List[Software]]
    Data: Optional[List[Data]]
    File: Optional[List[ArbitraryFile]]

class BagIt(Entity) :
    # A BagIt requires:
    #   - at least one recorded Data
    #       (otherwise, what is the point of the bag?)
    #   - arbitrary file definitions?
    #   - The input MEDFORD file
    #
    # For every file (recorded data or arbitrary file definition), MEDFORD
    #   parser has to:
    #   - create a sha-512 hash or sha-256 hash
    #   - copy into an appropriate subdirectory
    #       (default: data/
    #           alternative can be defined using the Subdirectory attribute)
    #   - write down name & final location into a manifest file:
    #       manifest-sha512.txt (or manifest-sha256.txt, depending on which was
    #                               used)
    #     in the format:
    #       checksum filepath
    #     NOTE: for now, don't allow any spaces, %, or linebreaks in file name
    @validator('File')
    @classmethod
    def check_singular_path_subdirectory(cls, values):
        for v in values:
            # TODO: Don't allow remote files, yet... Separate tag? RemoteFile?
            if len(v.Path) > 1 :
                raise ValueError("Please create a separate @File tag for each recorded file.")
            if len(v.Subdirectory) > 1:
                raise ValueError("MEDFORD does not currently support copying a file multiple times through one tag. " + 
                                "Please use a separate @File tag for each output file.")
            v = create_new_bagit_loc(v)
        return values

# Temporarily set to BaseModel instead of Entity for testing purposes.
class BCODMO(BaseModel):
    Data: List[Data]

    @validator('Data')
    @classmethod
    def check_at_least_one_recorded(cls, v) :
        if not any(map(lambda x: x.Flag == [DataTypeEnum.recorded], v)):
            raise ValueError('There must be at least 1 data field flagged as "recorded" for the BCO-DMO format,' +
                                ' to mark the new data being submitted.')
        return v

    Contributor: List[Contributor]
    Project: List[Project]
    Expedition: List[Expedition]

    # https://github.com/samuelcolvin/pydantic/issues/506
    # Check for at least one acceptable form of cruise identifier.
    @validator('Expedition')
    @classmethod
    def check_at_least_one_identifier(cls, v) :
        values = {key:value for key, value in v[0].__dict__.items() if not key.startswith('__') and not callable(key)}
        has_shipname = values['ShipName'] is not None and values['CruiseID'] is not None
        has_mooring = values['MooringID'] is not None 
        has_divenumber = values['DiveNumber'] is not None 
        if not any([has_shipname, has_mooring, has_divenumber]) :
            raise ValueError('BCO-DMO requires at least one cruise identifier. Your choices are: \n' +
                                '     ShipName and CruiseID, MooringID, or DiveNumber.')
        return v
    