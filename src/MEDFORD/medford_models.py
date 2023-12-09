from typing import List, Optional, Union, TypeVar, Tuple
import datetime
from pydantic import BaseModel as PydanticBaseModel, field_validator, model_validator, validator
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
    Note: OptDataT[str] = None

################################
# Field Models                 #
################################
class MEDFORDmodel(BaseModel) :
    desc: OptDataT[str]
    Version: DataT[str]
    @root_validator(pre=False, skip_on_failure=True)
    def check_version(cls, values) :
        if values['Version'] == [] :
            raise IncompleteDataError()

        actual_value = values['Version'][0][1]
        if actual_value not in all_versions :
            raise ValueError(f"Version {actual_value} is not a valid version")
        
        return values
    
class JournalModel(StrDescModel):
    Volume: DataT[int]
    Issue: DataT[str]
    # Issue types seen so far:
    # [month] [year] (connelly 2020)
    Pages: OptDataT[str] #TODO: Validation?

class DateModel(BaseModel):
    desc: Union[DataT[datetime.date], DataT[datetime.datetime]]
    Note: DataT[str]
    #changed type to note because type is a reserved keyword

class ContributorModel(StrDescModel) :
    ORCID: OptDataT[int] = None
    Association: OptDataT[str] = None
    Role: OptDataT[str] = None
    Email: OptDataT[str] #TODO: Email validation

    @root_validator(pre=False, skip_on_failure=True)
    def check_corresponding_has_contact(cls, v) :
        if v['Role'] is not None:
            roles = [r[1] for r in v['Role']]
            if "Corresponding Author" in roles and v["Email"] is None :
                raise IncompleteDataError("Corresponding Authors must have a provided validated email")
        return v

class FundingModel(StrDescModel) :
    ID: OptDataT[str] #TODO: Funding ID validation?

class KeywordModel(StrDescModel):
    pass

class SpeciesModel(StrDescModel):
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

class MethodModel(StrDescModel):
    Type: DataT[str]
    Company: OptDataT[str] = None
    Sample: OptDataT[str] = None

class ProjectModel(StrDescModel):
    pass

class ExpeditionModel(StrDescModel):
    ShipName: OptDataT[str] = None
    CruiseID: OptDataT[str] = None
    MooringID: OptDataT[str] = None
    DiveNumber: OptDataT[int] = None
    Synonyms: OptDataT[str] = None

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
    Path: OptDataT[str] = None
    Destination: OptDataT[str] = None
    URI: OptDataT[AnyUrl] = None
    outpath: str = ""
    @root_validator(pre=False, skip_on_failure=True)
    def check_singular_path_subdirectory(cls, values):
        # TODO: Don't allow remote files, yet... Separate tag? RemoteFile?
        if (values['Path'] != None and len(values['Path']) > 1) :
            raise ValueError("Please create a separate @File tag for each recorded file.")
        if (values['Destination'] != None and len(values['Destination']) > 1):
            raise ValueError("MEDFORD does not currently support copying a file multiple times through one tag. " + 
                            "Please use a separate @File tag for each output file.")
        #v = create_new_bagit_loc(v, "local")
        return values
    
    @root_validator(pre=False,skip_on_failure=True)
    def check_path_or_uri(cls, values) :
        if (values['Path'] == None or len(values['Path']) == 0) and (values['URI'] == None or len(values['URI']) == 0) :
            raise ValueError("Please provide a path or URI for the file.")
        if (values['Path'] != None and len(values['Path']) != 0) :
            values['type'] = 'local'
        else :
            values['type'] = 'remote'
        return values

class FreeformModel(BaseModel):
    class Config:
        extra = 'allow'
    pass

## Multi-Typed tags (data, code, paper)
class LocalBase(ArbitraryFile):
    Path: DataT[str]
    Destination: OptDataT[str] = None
    outpath: str =  ""

class RemoteBase(ArbitraryFile):
    URI: DataT[AnyUrl]
    Filename: DataT[str]
    outpath: str = ""

class D_Ref(RemoteBase) :
    # Should add conditional parsing based on certain types.
    # e.g. 'sra accession' should have some level of understanding of what that is, and what that means for the field 'filename',
    #       and expect minor token 'accession'
    Type: OptDataT[str] = None

class D_Copy(LocalBase) :
    Type: OptDataT[str] = None

class D_Primary(LocalBase) :
    Type: OptDataT[str] = None

class DataModel(BaseModel) :
    Ref: OptDataT[D_Ref] = None
    Copy: OptDataT[D_Copy] = None
    Primary: OptDataT[D_Primary] = None

class P_Ref(RemoteBase) :
    Link: OptDataT[AnyUrl] = None
    PMID: OptDataT[int] = None
    #Add a validator for PMID?
    DOI: OptDataT[datetime.date] = None

class P_Copy(StrDescModel) :
    Link: OptDataT[AnyUrl] = None
    PMID: OptDataT[int] = None
    #Add a validator for PMID?
    DOI: OptDataT[datetime.date] = None

class P_Primary(StrDescModel) :
    Link: OptDataT[AnyUrl] = None
    PMID: OptDataT[int] = None
    #Add a validator for PMID?
    DOI: OptDataT[datetime.date] = None

class PaperModel(BaseModel) :
    Ref: OptDataT[P_Ref] = None
    Copy: OptDataT[P_Copy] = None 
    Primary: OptDataT[P_Primary] = None

class S_Ref(RemoteBase):
    Type: DataT[str]
    Version: OptDataT[str] = None
    
class S_Copy(LocalBase):
    Type: DataT[str]
    Version: OptDataT[str] = None

class S_Primary(LocalBase):
    Type: DataT[str]
    Version: OptDataT[str] = None

class SoftwareModel(BaseModel): 
    Ref: OptDataT[S_Ref] = None
    Copy: OptDataT[S_Copy] = None
    Primary: OptDataT[S_Primary] = None

################################
# Overarching Model            #
################################
# Meant to store every single possible tag that we have defined
class Entity(BaseModel):
    MEDFORD: DataT[MEDFORDmodel]
    @field_validator('MEDFORD')
    def only_one_MEDFORD_block(cls, values) :
        if len(values) > 1 :
            raise ValueError("There can only be exactly one MEDFORD block in a file")
        return values

    Paper: OptDataT[PaperModel] = None
    Journal: OptDataT[JournalModel] = None
    Date: OptDataT[DateModel] = None
    Contributor: OptDataT[ContributorModel] = None
    Funding: OptDataT[FundingModel] = None 
    Keyword: OptDataT[KeywordModel] = None
    Species: OptDataT[SpeciesModel] = None
    Method: OptDataT[MethodModel] = None
    Software: OptDataT[SoftwareModel]  = None
    Data: OptDataT[DataModel] = None
    File: OptDataT[ArbitraryFile] = None
    Freeform: OptDataT[FreeformModel] = None

# Temporarily set to BaseModel instead of Entity for testing purposes.
class BCODMO(BaseModel):
    Data: DataT[DataModel]
    Contributor: DataT[ContributorModel]
    Project: DataT[ProjectModel]
    Expedition: DataT[ExpeditionModel]