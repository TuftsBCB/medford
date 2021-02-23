from pydantic import BaseModel, AnyUrl
from typing import List, Optional, Union
import datetime

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

class Data(StrDescModel) :
    Type: str
    URI: Optional[AnyUrl]

class Project(StrDescModel):
    pass


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


class BCODMO(Entity):
    Data: Data #How do we enforce a description?
    Contributor: Union[Contributor, List[Contributor]]
    Project: Project
    