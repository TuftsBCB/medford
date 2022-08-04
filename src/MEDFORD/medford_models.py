from typing import List, Optional, Union, TypeVar, Tuple
import datetime
from pydantic import BaseModel as PydanticBaseModel, validator
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
DatumT = Tuple[int, T]
DataT = List[DatumT[T]]
OptDataT = Optional[DataT[T]]

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
    desc: DataT[str] #TODO: Find a way to make an exception?
    Note: OptDataT[str]

################################
# Field Models                 #
################################
class MEDFORDmodel(BaseModel) :
    desc: OptDataT[str]
    Version: DataT[str]
    @root_validator
    def check_version(cls, values) :
        if values['Version'] == [] :
            raise IncompleteDataError()

        actual_value = values['Version'][0][1]
        if actual_value not in all_versions :
            raise ValueError(f"Version {actual_value} is not a valid version")
        
        return values
    
class Journal(StrDescModel):
    Volume: DataT[int]
    Issue: DataT[str]
    # Issue types seen so far:
    # [month] [year] (connelly 2020)
    Pages: OptDataT[str] #TODO: Validation?

class Date(BaseModel):
    desc: Union[DataT[datetime.date], DataT[datetime.datetime]]
    Note: DataT[str]
    #changed type to note because type is a reserved keyword

class Contributor(StrDescModel) :
    ORCID: OptDataT[int]
    Association: OptDataT[str]
    Role: OptDataT[str]
    Email: OptDataT[str] #TODO: Email validation

    @root_validator
    def check_corresponding_has_contact(cls, v) :
        if v['Role'] is not None:
            roles = [r[1] for r in v['Role']]
            if "Corresponding Author" in roles and v["Email"] is None :
                raise IncompleteDataError("Corresponding Authors must have a provided validated email")
        return v

class Funding(StrDescModel) :
    ID: OptDataT[str] #TODO: Funding ID validation?

class Keyword(StrDescModel):
    pass

class Species(StrDescModel):
    # Should it be Loc or Reef?
    # Consider following use case:
    # @Species-Reef Houwan
    # @Species-ReefCollection [..]
    # @Species-Reef Wanglitung 
    # @Species-ReefCollection [..]
    # Makes more sense than having two Locs and two ReefCollections. (Maybe also Reef should have the sub-token ReefCollection instead of having it be two separate minor tokens?)
    # Right now it doesn't validate that each reef has its own reefcollection.
    # Or maybe it should be listed as two separate species, then?
    Loc: DataT[str]
    ReefCollection: DataT[str] # TODO: Change to date with note?
    Cultured: DataT[str]
    CultureCollection: DataT[str]

class Method(StrDescModel):
    Type: DataT[str]
    Company: OptDataT[str]
    Sample: OptDataT[str]

class Project(StrDescModel):
    pass

class Expedition(StrDescModel):
    ShipName: OptDataT[str]
    CruiseID: OptDataT[str]
    MooringID: OptDataT[str]
    DiveNumber: OptDataT[int]
    Synonyms: OptDataT[str]

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
    Path: OptDataT[str]
    Destination: OptDataT[str]
    URI: OptDataT[AnyUrl]
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
    Path: DataT[str]
    Destination: OptDataT[str]
    outpath: str =  ""

class RemoteBase(StrDescModel):
    URI: DataT[AnyUrl]
    Filename: DataT[str]
    outpath: str = ""

class D_Ref(RemoteBase) :
    # Should add conditional parsing based on certain types.
    # e.g. 'sra accession' should have some level of understanding of what that is, and what that means for the field 'filename',
    #       and expect minor token 'accession'
    Type: OptDataT[str]

class D_Copy(LocalBase) :
    Type: OptDataT[str]

class D_Primary(LocalBase) :
    Type: OptDataT[str]

class Data(BaseModel) :
    Ref: OptDataT[D_Ref]
    Copy: OptDataT[D_Copy]
    Primary: OptDataT[D_Primary]

class P_Ref(RemoteBase) :
    Link: OptDataT[AnyUrl]
    PMID: OptDataT[int]
    #Add a validator for PMID?
    DOI: OptDataT[datetime.date]

class P_Copy(StrDescModel) :
    Link: OptDataT[AnyUrl]
    PMID: OptDataT[int]
    #Add a validator for PMID?
    DOI: OptDataT[datetime.date]

class P_Primary(StrDescModel) :
    Link: OptDataT[AnyUrl]
    PMID: OptDataT[int]
    #Add a validator for PMID?
    DOI: OptDataT[datetime.date]

class Paper(BaseModel) :
    Ref: OptDataT[P_Ref]
    Copy: OptDataT[P_Copy]
    Primary: OptDataT[P_Primary]

class S_Ref(RemoteBase):
    Type: DataT[str]
    Version: OptDataT[str]
    
class S_Copy(LocalBase):
    Type: DataT[str]
    Version: OptDataT[str]

class S_Primary(LocalBase):
    Type: DataT[str]
    Version: OptDataT[str]

class Software(BaseModel): 
    Ref: OptDataT[S_Ref]
    Copy: OptDataT[S_Copy]
    Primary: OptDataT[S_Primary]

################################
# Overarching Model            #
################################
# Meant to store every single possible tag that we have defined
class Entity(BaseModel):
    MEDFORD: DataT[MEDFORDmodel]
    @validator('MEDFORD', pre=True)
    def only_one_MEDFORD_block(cls, values) :
        if len(values) > 0 :
            raise ValueError("There can only be exactly one MEDFORD block in a file")
        return values

    Paper: OptDataT[Paper]
    Journal: OptDataT[Journal]
    Date: OptDataT[Date]
    Contributor: OptDataT[Contributor]
    Funding: OptDataT[Funding]
    Keyword: OptDataT[Keyword]
    Species: OptDataT[Species]
    Method: OptDataT[Method]
    Software: OptDataT[Software]
    Data: OptDataT[Data]
    File: OptDataT[ArbitraryFile]
    Freeform: OptDataT[Freeform]

# Temporarily set to BaseModel instead of Entity for testing purposes.
class BCODMO(BaseModel):
    Data: DataT[Data]
    Contributor: DataT[Contributor]
    Project: DataT[Project]
    Expedition: DataT[Expedition]