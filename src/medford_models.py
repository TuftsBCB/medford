from pydantic import BaseModel, AnyUrl, validator
from typing import List, Optional, Union, Iterable
import datetime
from enum import Enum

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
    Type: List[str]
    ORCID: Optional[List[int]]
    Assocation: Optional[List[str]]
    Role: Optional[List[str]]
    Email: Optional[List[str]] #TODO: Email validation

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

################################
# Overarching Model            #
################################
class Entity(BaseModel):
    Paper: List[Paper]
    Journal: List[Journal]
    Date: List[Date]
    Contributor: List[Contributor]
    Keyword: List[Keyword]
    Species: List[Species]
    Method: List[Method]
    Software: List[Software]
    Data: List[Data]

# Temporarily set to BaseModel instead of Entity for testing purposes.
class BCODMO(BaseModel):
    Data: List[Data]

    @validator('Data')
    @classmethod
    def check_at_least_one_recorded(cls, v) :
        if not any(map(lambda x: x.Flag == [DataTypeEnum.recorded], v)):
            raise ValueError('There must be at least 1 data field flagged as "recorded" for the BCO-DMO format,' +
                                ' to mark the new data being submitted.')

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
    