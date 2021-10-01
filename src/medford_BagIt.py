from medford_models import *
from shutil import copyfile
from typing import Callable, List, Optional, Tuple, Union, Iterable
from medford_detailparser import detailparser
import hashlib
import errno
import itertools
from copy import Error, deepcopy

## Helper Functions
### Hashing
def calculate_sha_512(filename) :
    with open(filename, "rb") as f:
        bytes = f.read()
        hash = hashlib.sha512(bytes).hexdigest()
    return hash

def calculate_sha_256(filename) :
    with open(filename, "rb") as f:
        bytes = f.read()
        hash = hashlib.sha256(bytes).hexdigest()
    return hash

### Settings
class bagit_settings:
    prefix = "data/"
    regex = "^[^%\s]+$"
    output_location = ""

LocalFile = Union[ArbitraryFile, D_Copy, D_Primary, S_Copy, S_Primary]
RemoteFile = Union[ArbitraryFile, D_Ref, S_Ref]

### Complex Helpers
def manage_local_file(inp_file: LocalFile) -> Tuple[str, int]:
    """
    Given a "local" file (file with a defined PATH), defines its new bag-relative location, copies it to that location, and adjusts its internal stored path to that new location. Then, returned the calculated SHA of the file.
    
    INPUT:
        **inp_file** (required) : the pydantic model of the file's information. Must have a Name and a non-empty Path. Subdirectory may or may not be defined.
    
    OUTPUT:
        integer - the calculated sha of the copied file.

    SIDE EFFECTS:
        - changes inp_file's path, deletes subdirectory if defined.
        - creates a new file in the user's system, under the BAG output location defined by bagit_settings.output_location
    """
    copy_location, relative_location = create_bagit_loc(inp_file)
    copy_local_file(inp_file, copy_location)
    mutate_local_file(inp_file, relative_location)
    return (relative_location + inp_file.Name[0], calculate_sha_512(copy_location + inp_file.Name[0]))

def create_bagit_loc(inp_file: Union[LocalFile, RemoteFile]) -> Tuple[str, str]:
    """Given a either a remote or local file, defines its new bag-relative location.
    
    INPUT:
        inp_file (r)    : the pydantic model of the file's information. Must have a Name. Subdirectory may or may not be defined.

    OUTPUT:
        Tuple[str,str] - A tuple of two strings, the first being the full run-relative path to copy the given file to and the second being the new bag-relative location of the file after copy. Both of these are generated using the prefix and bag_location defined in bagit_settings.
    """
    relative_location = bagit_settings.prefix
    if inp_file.Subdirectory is not None and len(inp_file.Subdirectory) > 0 :
        if inp_file.Subdirectory[0][-1] != "/" :
            inp_file.Subdirectory[0] = inp_file.Subdirectory[0] + "/"
        relative_location = relative_location + inp_file.Subdirectory[0]
    return (bagit_settings.output_location + relative_location, relative_location)

def copy_local_file(inp_file: LocalFile, copy_location: str) -> Tuple[bool, Union[None, Error]]:
    """
    Given a "local" file (file with a defined PATH), copies it from its original path to its bag-relative location.
    
    INPUT: 
        **inp_file** (required) : the pydantic model of the file's information. Must have a Name and a Path.
        **copy_location** (required) : the location that was determined to be the bag-relative location this file should be copied to.
    
    OUTPUT:
        Tuple[bool, None | Error] - a tuple where the first bool represents whether or not the copy was successful. If the copy was unsuccessful (bool is False), the error message is stored in the second entry of the Tuple.

    SIDE EFFECTS:
        - Copies the local file from Path to _output_path.
    """
    try:
        os.makedirs(copy_location, exist_ok=True)
        copyfile(inp_file.Path[0], copy_location + inp_file.Name[0])
        return((True, None))
    except OSError as e:
        return((False, e))

def mutate_local_file(inp_file: LocalFile, relative_location: str) -> None :
    """
    Given a local file and its relative location, adjusts its pydantic model to represent the new bag-relative location.

    INPUT:
        **inp_file** (required) : the pydantic model of the file's information. Must have a Name.
        **relative_location** (required) : the new location of the copied file, relative to the root of the bag.
    
    SIDE EFFECTS:
        - changes Path in input_file to point to relative_location + inp_file.Name[0], and deletes Subdirectory if defined.
    """
    inp_file.Path = [relative_location + inp_file.Name[0]]
    inp_file.Subdirectory = None

def manage_remote_file(inp_file: RemoteFile) -> str:
    """Creates the fetch.txt line for a file

    Given a "remote file", generates the line to be entered into fetch.txt.

    INPUT:
        inp_file (r)    : the pydantic model of the file's information. Must have a Name and a URI.
    
    OUTPUT:
        str     - a string that fulfills all the requirements for fetchtxt, formatted as follows:
            (inp_file URI)  -   (inp_file output location)
    """
    copy_location, relative_location = create_bagit_loc(inp_file)
    fetchstring = inp_file.URI[0] + "\t-\t" + relative_location + inp_file.Name[0]
    return fetchstring

def perform_medford_munging(mfd_input: str, howto_write: Callable[[ArbitraryFile, str],None]) -> Tuple[str, int] :
    # TODO: foolproof way of getting medford file name
    mfd_name = os.path.basename(mfd_input)
    mfd_model = ArbitraryFile(desc = ['Medford File'], Name = [mfd_name])
    output_location, relative_location = create_bagit_loc(mfd_model)
    mutate_local_file(mfd_model, relative_location)
    howto_write(mfd_model, output_location + mfd_name)

    sha = calculate_sha_512(output_location + mfd_name)
    return((relative_location + mfd_name, sha))

def write_manifest(sha_entries) :
    with open(bagit_settings.output_location + "manifest-sha512.txt", 'w') as f:
        for entry in sha_entries:
            f.write("%s %s" % entry)
            f.write("\n")

def write_fetch(fetch_entries) :
    with open(bagit_settings.output_location + "fetch.txt", 'w') as f:
        for entry in fetch_entries :
            f.write(entry)
            f.write("\n")

## Models
class BagIt(Entity) :
    Data: List[Data]
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
            #v = create_new_bagit_loc(v, "local")
        return values

## Runners
def runBagitMode(parameters, medford_input) :
    bagdir = medford_input + "_BAG/"
    if not os.path.isdir(bagdir) :
        os.mkdir(bagdir)
    if not os.path.isdir(bagdir + "data") :
        os.mkdir(bagdir + "data/")
    
    # Deep copying parameters because we are about to do a LOT of mutation
    _parameters = deepcopy(parameters)
    bagit_settings.output_location = bagdir

    sha_entries = []
    fetch_entries = []
    if _parameters.File is not None and len(_parameters.File) > 0 :
        for possible_file in _parameters.File :
            if possible_file.Path is not None :
                sha_entries.append(manage_local_file(possible_file))
            elif possible_file.URI is not None :
                fetch_entries.append(manage_remote_file(possible_file))
            else :
                raise NotImplementedError #fix error type

    local_named = []
    remote_named = []
    if _parameters.Data is not None :
        local_named = itertools.chain(itertools.dropwhile(lambda x: x is None, [_parameters.Data[0].Copy, _parameters.Data[0].Primary]))
        remote_named = _parameters.Data[0].Ref if _parameters.Data[0].Ref is not None else []
    if _parameters.Software is not None :
        local_named = local_named + itertools.chain(itertools.dropwhile(lambda x: x is None, [_parameters.Data[0].Software, _parameters.Software[0].Primary]))
        remote_named = remote_named + _parameters.Software[0].Ref if _parameters.Software[0].Ref is not None else []
    
    for lf in local_named:
        sha_entries.append(manage_local_file(lf))

    for rf in remote_named:
        fetch_entries.append(manage_remote_file(rf))

    if _parameters.File is None:
        _parameters.File = []

    def write_medford_file(mfd_model, final_location) :
        _parameters.File.append(mfd_model)
        detailparser.write_from_dict(_parameters.dict(), final_location)

    sha_entries.append(perform_medford_munging(medford_input, write_medford_file))
    
    write_manifest(sha_entries)
    write_fetch(fetch_entries)

    #zip_all_files()
