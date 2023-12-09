import typing
from MEDFORD.medford_models import *
from shutil import copyfile, make_archive
from typing import Callable, List, Optional, Tuple, Union, Iterable
from MEDFORD.medford_detailparser import detailparser
import hashlib
import itertools
import os
from copy import Error, deepcopy
from pathlib import Path, PurePath

## Models
class BagIt(Entity) :
    Data: OptDataT[DataModel]
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
    _bagdir: Path
    _datadir: Path

    @classmethod
    def set_datadir(cls, input_dir:Path) -> None :
        bagit_settings._datadir = input_dir
    
    @classmethod
    def get_datadir(cls) -> Path :
        if cls._datadir == "" :
            raise Error("Data directory not set")
        return cls._datadir

    @classmethod
    def set_bagdir(cls, input_dir:Path) -> None :
        cls._bagdir = input_dir
    
    @classmethod
    def get_bagdir(cls) -> Path :
        if cls._bagdir == "" :
            raise Error("Bag directory not set")
        return cls._bagdir

LocalFile = Union[ArbitraryFile, D_Copy, D_Primary, S_Copy, S_Primary]
RemoteFile = Union[ArbitraryFile, D_Ref, S_Ref]

### Complex Helpers
def add_outpath(inp_file: Union[LocalBase, RemoteBase], type:str) -> Union[LocalBase, RemoteBase]:
    """Given a either a remote or local file, defines its new bag-relative location.
    
    INPUT:
        inp_file (r)    : the pydantic model of the file's information. Must have a Name. Subdirectory may or may not be defined.

    OUTPUT:
        LocalFile | RemoteFile - the same file, but with a new outpath defined.
    """
    datadir = bagit_settings.get_datadir()
    if type == "local":
        # 1. create the novel location
        if inp_file.Destination is not None :
            # TODO: separate this out into a separate function. (filename mngmt utils?)
            if inp_file.Destination[0][1][0] == "/" :
                shortdest = inp_file.Destination[0][1][2:]
            else :
                shortdest = inp_file.Destination[0][1]
            inp_file.outpath = [(inp_file.Destination[0][0], datadir.joinpath(shortdest))]
        else :
            inp_file.Destination = [(-1, datadir.joinpath(Path(inp_file.Path[0][1])).name)]
            inp_file.outpath = [(-1, datadir.joinpath(os.path.basename(inp_file.Path[0][1])))]
    elif type == "remote":
        inp_file.outpath = [(inp_file.Filename[0][0], "data/" + inp_file.Filename[0][1])]
    
    return inp_file

def copy_local_file(inp_file: str, copy_location: str) -> Tuple[bool, Union[None, Error]]:
    """
    Given a "local" file (file with a defined PATH), copies it from its original path to its bag-relative location.
    
    INPUT: 
        **inp_file** (required) : str representing the current location of the file in the operating system
        **copy_location** (required) : the location that was determined to be the bag-relative location this file should be copied to.
    
    OUTPUT:
        Tuple[bool, None | Error] - a tuple where the first bool represents whether or not the copy was successful. If the copy was unsuccessful (bool is False), the error message is stored in the second entry of the Tuple.

    SIDE EFFECTS:
        - Copies the local file from Path to _output_path.
    """
    try:
        copy_directory = os.path.dirname(copy_location)
        os.makedirs(copy_directory, exist_ok=True)
        copyfile(inp_file, copy_location)
        return((True, None))
    except OSError as e:
        return((False, e))

def mutate_local_file(inp_file: LocalBase) -> LocalBase :
    """
    Given a local file and its relative location, adjusts its pydantic model to represent the new bag-relative location.

    INPUT:
        **inp_file** (required) : the pydantic model of the file's information.
    
    SIDE EFFECTS:
        - changes Path in input_file to point to relative_location + inp_file.Name[0], and deletes Subdirectory if defined.
    """
    
    inp_file.Path = inp_file.Destination
    inp_file.outpath = None
    inp_file.Destination = None
    if 'type' in inp_file.__dict__.keys() :
        del inp_file.type
    return inp_file

def mutate_remote_file(inp_file: RemoteBase) -> None:
    inp_file.Filename = inp_file.outpath
    inp_file.outpath = None
    if 'type' in inp_file.__dict__.keys() :
        del inp_file.type
    return inp_file


def manage_remote_file(inp_file: RemoteBase) -> str:
    """Creates the fetch.txt line for a file

    Given a "remote file", generates the line to be entered into fetch.txt.

    INPUT:
        inp_file (r)    : the pydantic model of the file's information. Must have a Name and a URI.
    
    OUTPUT:
        str     - a string that fulfills all the requirements for fetchtxt, formatted as follows:
            (inp_file URI)  -   (inp_file output location)
    """
    outpath = inp_file.outpath[0][1]

    fetchstring = str(inp_file.URI[0][1]) + "\t-\t" + outpath
    return fetchstring

def perform_medford_munging(mfd_input: str, howto_write: Callable[[LocalBase, str],None], parameters: BagIt) -> Tuple[str, str] :
    """Create an entry for the current medford file, write the adjusted file into the bag.

    Given the current medford file location, creates an ArbitraryFile entry for the medford. Then, calculates what its location inside the bag should be and modifies the ArbitraryFile entry appropriately. Then uses the passed howto_write function to write the fully adjusted medford file to the correct location before finally returning all the information required for the manifest.

    INPUT:
        mfd_input (r)   : (str) The location of the .mfd file that MEDFORD is currently running on.
        howto_write (r) : (Callable[[ArbitraryFile, str], None]) A function that given the medford pydantic model and an output location, writes the adjusted medford file in medford format to that location.
        
    OUTPUT:
        Tuple[str, int] : A tuple containing all of the information required for the manifest (bag-relative location and sha integer.))
    """
    # TODO: foolproof way of getting medford file name
    arb_file_params = {
        'desc': [(-1, 'Medford File')],
        'Path': [(-1, str(Path(mfd_input)))]
    }
    #mfd_model = ArbitraryFile(desc = [(-1,'Medford File')], Path = [(-1,mfd_input)])
    arb_file_model = LocalBase(**arb_file_params)
    arb_file_model = add_outpath(arb_file_model, 'local')
    outpath = arb_file_model.outpath[0][1] # store the outpath rq (not technically necessary)

    # reiterate that this is a LocalBase file
    arb_file_model = typing.cast(LocalBase,arb_file_model)
    sha = calculate_sha_512(arb_file_model.Path[0][1])
    arb_file_model = mutate_local_file(arb_file_model) # remember: this mutates!!! (how do I flag that? NoneType return? Should I make this not mutate but return a new object with the values changed? Probably...)
    
    howto_write(arb_file_model, outpath, parameters)

    #return(arb_file_model, sha)
    return (arb_file_model.Path[0][1], sha)

def write_manifest(sha_entries) :
    outdir = bagit_settings.get_bagdir()
    with open(outdir.joinpath("manifest-sha512.txt"), 'w') as f:
        for entry in sha_entries:
            f.write(entry)
            f.write("\n")

def write_fetch(fetch_entries) :
    outdir = bagit_settings.get_bagdir()
    with open(outdir.joinpath("fetch.txt"), 'w') as f:
        for entry in fetch_entries :
            f.write(entry)
            f.write("\n")

def zip_all_files(mfd_input) :
    outdir = bagit_settings.get_bagdir()
    # WARNING: VERY fragile; not tested on windows or macs whatsoever.
    zipname = os.path.splitext(os.path.basename(mfd_input))[0]
    dirname = os.path.dirname(mfd_input)
    make_archive(dirname + "/" + zipname, "zip", outdir)


## Runners
def runBagitMode(parameters: BaseModel, medford_input: str) :
    # Goals for BagIt processing:
    #   1. generate the bagIt output directory string
    #   2. create empty fetch.txt file
    #   3. create empty manifest-sha512.txt file
    #   4. Identify all the files to be included in the bag
    #       a. arbitrary data files :
    #            i. with a PATH defined
    #            ii. with a URI defined
    #       b. Data files:
    #            i. copy            : has a PATH, might have a URI      : copy the file from the PATH to the bag-relative location & add to sha
    #            ii. primary        : has a PATH, shouldn't have a URI  : copy the file from the PATH to the bag-relative location & add to sha
    #            iii. reference     : has a URI, shouldn't have a PATH  : add to the fetch.txt file
    #       c. Software files:
    #          i. copy            : has a PATH, might have a URI      : copy the file from the PATH to the bag-relative location & add to sha
    #          ii. primary        : has a PATH, shouldn't have a URI  : copy the file from the PATH to the bag-relative location & add to sha
    #          iii. reference     : has a URI, shouldn't have a PATH  : add to the fetch.txt file
    #   5. Modify MEDFORD file s.t. PATHs now all point to novel locations
    #   6. Copy MEDFORD into the bag
    #   7. add MEDFORD file to manifest-sha512.txt
    #   8. zip entire bag


    # generating the output directory strong
    # get the basename of the file
    base_filename = medford_input.stem

    bagdir = medford_input.with_name(base_filename + "_BAG")
    #bagdir = medford_input + "_BAG/"
    if not os.path.isdir(bagdir) :
        os.mkdir(bagdir)
    bagit_settings.set_bagdir(bagdir)

    bagdatadir = bagdir.joinpath("data")
    if not os.path.isdir(bagdatadir) :
        os.mkdir(bagdatadir)
    bagit_settings.set_datadir(bagdatadir)

    # Deep copying parameters because we are about to do a LOT of mutation
    _parameters = deepcopy(parameters)
    bagit_settings.output_location = bagdir

    # create empty fetch.txt file

    fetch_lines = []

    # create empty manifest-sha512.txt file
    sha_lines = []

    # Identify all the files to be included in the bag
    local_files = []
    remote_files = []
    
    # arbitrary files
    if 'File' in _parameters.model_fields and _parameters.File is not None and len(_parameters.File) > 0:
        for possible_file in _parameters.File :
            if possible_file[1].type == 'local' :
                local_files.append(possible_file)
            elif possible_file[1].type == 'remote' :
                remote_files.append(possible_file)
            else :
                raise NotImplementedError #fix error type

    # data & software files
    local_named = []
    remote_named = []
    if 'Data' in _parameters.model_fields and _parameters.Data is not None :
        local_named = list(itertools.chain.from_iterable(itertools.dropwhile(lambda x: x is None, [_parameters.Data[0][1].Copy, _parameters.Data[0][1].Primary])))
        remote_named = _parameters.Data[0][1].Ref if _parameters.Data[0][1].Ref is not None else []
    if 'Software' in _parameters.model_fields and _parameters.Software is not None :
        local_named = local_named + list(itertools.chain.from_iterable(itertools.dropwhile(lambda x: x is None, [_parameters.Software[0][1].Copy, _parameters.Software[0][1].Primary])))
        remote_named = remote_named + _parameters.Software[0][1].Ref if _parameters.Software[0][1].Ref is not None else []

    all_local_files = itertools.chain(local_named, local_files)
    modified_locals = []
    for lf in all_local_files :
        lf = lf[1]
        lf = add_outpath(lf, 'local')
        curpath = lf.Path[0][1]
        curout = lf.outpath[0][1]
        dest = lf.Destination[0][1]
        
        # 2. create the sha & add to manifest
        lf_sha = calculate_sha_512(curpath)
        sha_lines.append("%s %s" % (dest, lf_sha))

        # 3. copy the file to the novel location
        copy_local_file(curpath, curout)

        # 4. update the internal information (path -> new location)
        lf = mutate_local_file(lf)
        
        # store the modified local file
        modified_locals.append(lf)
        
    all_remote_files = itertools.chain(remote_named, remote_files)
    for rf in all_remote_files :
        rf = rf[1]
        rf = add_outpath(rf, 'remote')

        rf_fetch = manage_remote_file(rf)
        rf = mutate_remote_file(rf)
        fetch_lines.append(rf_fetch)

    # ???
    def write_medford_file(new_local_model:LocalBase, final_location:str , original_bag:BagIt) :
        #if 'File' not in _parameters.keys() :
        #    _parameters['File'] = []
        #_parameters['File'].append((-1,new_local_model))
        #new_model = BagIt(**_parameters)
        if 'File' not in original_bag.model_fields or original_bag.File is None :
            original_bag.File = []
        original_bag.File.append((-1, new_local_model))

        detailparser.write_from_model(original_bag, final_location)

    mfd_path, mfd_sha = perform_medford_munging(medford_input, write_medford_file, _parameters)
    sha_lines.append("%s %s" % (mfd_path, mfd_sha))
    
    write_manifest(sha_lines)
    write_fetch(fetch_lines)

    zip_all_files(medford_input)

