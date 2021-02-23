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
    desc: str
    Note: Optional[Union[str, List[str]]]

################################
# Field Models                 #
################################
class Paper(StrDescModel):
    Link: Optional[AnyUrl]
    PMID: Optional[int]
    #Add a validator for PMID?
    DOI: Optional[datetime.date]

class Journal(StrDescModel):
    Volume: int
    Issue: int
    Pages: Optional[str] #TODO: Validation?

class Date(BaseModel):
    desc: Union[datetime.date, datetime.datetime, str]
    Note: str 
    #changed type to note because type is a reserved keyword

class Contributor(StrDescModel) :
    Type: str
    ORCID: Optional[int]
    Assocation: Optional[str]
    Role: Optional[str]
    Email: Optional[str] #TODO: Email validation

class Keyword(StrDescModel):
    pass

class Species(StrDescModel):
    Loc: str
    ReefCollection: str # TODO: Change to date with note?
    Cultured: str
    CultureCollection: str

class Method(StrDescModel):
    Type: str
    Company: Optional[str]
    Sample: Optional[str]

class Software(StrDescModel) :
    Type: str
    Version: Optional[str]

class DataTypeEnum(str, Enum):
    # TODO : How do we avoid caring about capitalization, tho?
    recorded = "recorded"
    referenced = "referenced"

class Data(StrDescModel) :
    Type: str
    URI: Optional[AnyUrl]
    Flag: DataTypeEnum = DataTypeEnum.referenced

class Project(StrDescModel):
    pass

class Cruise(StrDescModel):
    ShipName: Optional[str]
    CruiseID: Optional[str]
    MooringID: Optional[str]
    DiveNumber: Optional[int]
    Synonyms: Optional[Iterable[str]]

################################
# Overarching Model            #
################################
class Entity(BaseModel):
    Paper: Paper
    Journal: Journal
    Date: Union[Date, List[Date]]
    Contributor: Union[Contributor, List[Contributor]]
    Keyword: Union[Keyword, List[Keyword]]
    Species: Union[Species, List[Species]]
    Method: Union[Method, List[Method]]
    Software: Union[Software, List[Software]]
    Data: Union[Data, List[Data]]

# Temporarily set to BaseModel instead of Entity for testing purposes.
class BCODMO(BaseModel):
    Data: Union[Data, List[Data]]

    @validator('Data')
    def check_at_least_one_recorded(cls, v) :
        if isinstance(v, List) :
            if not any(map(lambda x: x.Flag == DataTypeEnum.recorded, v)):
                raise ValueError('There must be at least 1 data field flagged as "recorded" for the BCO-DMO format,' +
                                 ' to mark the new data being submitted.')
        else :
            if not v.Flag == DataTypeEnum.recorded :
                raise ValueError('Data entry must be flagged as "recorded" for the BCO-DMO format, to represent the ' + 
                                ' new data being submitted.')

    Contributor: Union[Contributor, List[Contributor]]
    Project: Project
    Cruise: Cruise

    # https://github.com/samuelcolvin/pydantic/issues/506
    # Check for at least one acceptable form of cruise identifier.
    @validator('Cruise')
    def check_at_least_one_identifier(cls, v) :
        values = {key:value for key, value in v.__dict__.items() if not key.startswith('__') and not callable(key)}
        has_shipname = values['ShipName'] is not None and values['CruiseID'] is not None
        has_mooring = values['MooringID'] is not None 
        has_divenumber = values['DiveNumber'] is not None 
        if not any([has_shipname, has_mooring, has_divenumber]) :
            raise ValueError('BCO-DMO requires at least one cruise identifier. Your choices are: \n' +
                                '     ShipName and CruiseID, MooringID, or DiveNumber.')
    