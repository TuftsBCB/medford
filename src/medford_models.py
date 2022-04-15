from typing import List, Optional, Union, TypeVar, Tuple
import datetime
from pydantic import BaseModel as PydanticBaseModel
from pydantic import AnyUrl, root_validator

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

T = TypeVar('T')
OptListT = Optional[List[Tuple[int, T]]]
ListT = List[Tuple[int, T]]

class BaseModel(PydanticBaseModel) :
    class Config:
        extra = 'allow'

class IncompleteDataError(ValueError):
    code = "incomplete_data_error"

all_versions = ["1.0"]
################################
# Helper Models                #
################################
class StrDescModel(BaseModel):
    desc: ListT[str] #TODO: Find a way to make an exception?
    Note: OptListT[str]

################################
# Field Models                 #
################################
class MEDFORDmodel(BaseModel) :
    desc: OptListT[str]
    Version: ListT[str]
    @root_validator
    def check_version(cls, values) :
        if values['Version'] == [] :
            raise IncompleteDataError()

        actual_value = values['Version'][0][1]
        if actual_value not in all_versions :
            raise ValueError(f"Version {actual_value} is not a valid version")
        
        return values
    
class Journal(StrDescModel):
    Volume: ListT[int]
    Issue: ListT[int]
    Pages: OptListT[str] #TODO: Validation?

class Date(BaseModel):
    desc: Union[ListT[datetime.date], ListT[datetime.datetime]]
    Note: ListT[str]
    #changed type to note because type is a reserved keyword

class Contributor(StrDescModel) :
    ORCID: OptListT[int]
    Assocation: OptListT[str]
    Role: OptListT[str]
    Email: OptListT[str] #TODO: Email validation

    @root_validator
    def check_corresponding_has_contact(cls, v) :
        if v['Role'] is not None:
            roles = [r[1] for r in v['Role']]
            if "Corresponding Author" in roles and v["Email"] is None :
                raise IncompleteDataError("Corresponding Authors must have a provided validated email")
        return v

class Funding(StrDescModel) :
    ID: OptListT[str] #TODO: Funding ID validation?

class Keyword(StrDescModel):
    pass

class Species(StrDescModel):
    Loc: ListT[str]
    ReefCollection: ListT[str] # TODO: Change to date with note?
    Cultured: ListT[str]
    CultureCollection: ListT[str]

class Method(StrDescModel):
    Type: ListT[str]
    Company: OptListT[str]
    Sample: OptListT[str]

class Project(StrDescModel):
    pass

class Expedition(StrDescModel):
    ShipName: OptListT[str]
    CruiseID: OptListT[str]
    MooringID: OptListT[str]
    DiveNumber: OptListT[int]
    Synonyms: OptListT[str]

    #def check_at_least_one_identifier(cls, v) :
    #    values = {key:value for key, value in v[0].__dict__.items() if not key.startswith('__') and not callable(key)}
    #    has_shipname = values['ShipName'] is not None and values['CruiseID'] is not None
    #    has_mooring = values['MooringID'] is not None 
    #    has_divenumber = values['DiveNumber'] is not None 
    #    if not any([has_shipname, has_mooring, has_divenumber]) :
    #        raise ValueError('BCO-DMO requires at least one cruise identifier. Your choices are: \n' +
    #                            '     ShipName and CruiseID, MooringID, or DiveNumber.')
    #    return v

class ArbitraryFile(StrDescModel):
    #todo: change to filename
    Path: OptListT[str]
    Destination: OptListT[str]
    URI: OptListT[AnyUrl]
    outpath: str = ""
    @root_validator
    def check_singular_path_subdirectory(cls, values):
        # TODO: Don't allow remote files, yet... Separate tag? RemoteFile?
        if (values['Path'] != None and len(values['Path']) > 1) :
            raise ValueError("Please create a separate @File tag for each recorded file.")
        if (values['Destination'] != None and len(values['Destination']) > 1):
            raise ValueError("MEDFORD does not currently support copying a file multiple times through one tag. " + 
                            "Please use a separate @File tag for each output file.")
        #v = create_new_bagit_loc(v, "local")
        return values
    
    @root_validator
    def check_path_or_uri(cls, values) :
        if (values['Path'] == None or len(values['Path']) == 0) and (values['URI'] == None or len(values['URI']) == 0) :
            raise ValueError("Please provide a path or URI for the file.")
        if (values['Path'] != None and len(values['Path']) != 0) :
            values['type'] = 'local'
        else :
            values['type'] = 'remote'
        return values

class Freeform(BaseModel):
    class Config:
        extra = 'allow'
    pass

## Multi-Typed tags (data, code, paper)
class LocalBase(StrDescModel):
    Path: ListT[str]
    Destination: OptListT[str]
    outpath: str =  ""

class RemoteBase(StrDescModel):
    URI: ListT[AnyUrl]
    Filename: ListT[str]
    outpath: str = ""

class D_Ref(RemoteBase) :
    Type: OptListT[str]

class D_Copy(LocalBase) :
    Type: OptListT[str]

class D_Primary(LocalBase) :
    Type: OptListT[str]

class Data(BaseModel) :
    Ref: OptListT[D_Ref]
    Copy: OptListT[D_Copy]
    Primary: OptListT[D_Primary]

class P_Ref(RemoteBase) :
    Link: OptListT[AnyUrl]
    PMID: OptListT[int]
    #Add a validator for PMID?
    DOI: OptListT[datetime.date]

class P_Copy(StrDescModel) :
    Link: OptListT[AnyUrl]
    PMID: OptListT[int]
    #Add a validator for PMID?
    DOI: OptListT[datetime.date]

class P_Primary(StrDescModel) :
    Link: OptListT[AnyUrl]
    PMID: OptListT[int]
    #Add a validator for PMID?
    DOI: OptListT[datetime.date]

class Paper(BaseModel) :
    Ref: OptListT[P_Ref]
    Copy: OptListT[P_Copy]
    Primary: OptListT[P_Primary]

class S_Ref(RemoteBase):
    Type: ListT[str]
    Version: OptListT[str]
    
class S_Copy(LocalBase):
    Type: ListT[str]
    Version: OptListT[str]

class S_Primary(LocalBase):
    Type: ListT[str]
    Version: OptListT[str]

class Software(BaseModel): 
    Ref: OptListT[S_Ref]
    Copy: OptListT[S_Copy]
    Primary: OptListT[S_Primary]

################################
# Overarching Model            #
################################
# Meant to store every single possible tag that we have defined
class Entity(BaseModel):
    MEDFORD: ListT[MEDFORDmodel]
    Paper: OptListT[Paper]
    Journal: OptListT[Journal]
    Date: OptListT[Date]
    Contributor: OptListT[Contributor]
    Funding: OptListT[Funding]
    Keyword: OptListT[Keyword]
    Species: OptListT[Species]
    Method: OptListT[Method]
    Software: OptListT[Software]
    Data: OptListT[Data]
    File: OptListT[ArbitraryFile]
    Freeform: OptListT[Freeform]

# Temporarily set to BaseModel instead of Entity for testing purposes.
class BCODMO(BaseModel):
    Data: List[Data]
    Contributor: List[Contributor]
    Project: List[Project]
    Expedition: List[Expedition]