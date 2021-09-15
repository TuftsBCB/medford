from medford_models import *
from shutil import copyfile
from typing import List, Optional, Union, Iterable
import hashlib
import errno

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

### Complex Helpers
def adjust_mfd_add_to_local(parameters, mfd_file) :
    
    with open(mfd_file, 'a') as f:
        f.write("")
        f.write("#Added by medford-BagIt parser")
        f.write("@File Medford File")
        f.write("@File-Path data/" + mfd_file)
    


def create_new_bagit_loc(FileObj, fileType) :
    """
    Adjusts a given File object such that it is guaranteed that the file fulfills all requirements for copying.

    These requirements are:
        - valid input file (see valid_input_file)
        - valid output location (see valid_filename_bagit)
    
    It then defines the File object's NewName parameter to contain a string representation of the location it should be
        copied to.
    """
    if fileType == "remote" :
        # copy the file using FileObj.URI
        # http = urllib3.PoolManager()
        filename = os.path.basename(FileObj.URI[0])
        #request = http.request('GET', FileObj.URI[0])
        #if (request.status != 200) :
        #    raise ValueError("Cannot reach file...")
        #with open(filename, "wb") as f:
        #    f.write(request.data)
        # Strip out to just the name of the file
        # Then generate output name and continue as expected
        FileObj.Path = [filename]

    if FileObj.Subdirectory :
        output_name = bagit_settings.prefix + generate_output_name(FileObj.Subdirectory[0], FileObj.Path[0])
    else :
        output_name = bagit_settings.prefix + "/" + FileObj.Path[0]
    FileObj.output_path = output_name
    
    #can_write_new, reason = valid_filename_bagit(output_name)
    #if not can_write_new:
    #    raise ValueError("Cannot copy file, reason: " + reason)
    #can_read_old, reason = valid_input_file(FileObj.Path[0])
    #if not can_read_old :
    #    raise ValueError("Cannot copy file, reason: " + reason)
    #FileObj.bagName = output_name
    #return FileObj

def create_fetch_txt(remote_files) :
    # From the RFC documentation:
    # (https://datatracker.ietf.org/doc/html/rfc8493#section-2.2.3)

    # The fetch file MUST be named "fetch.txt".  Every file listed in the
    # fetch file MUST be listed in every payload manifest.  A fetch file
    # MUST NOT list any tag files.

    # Each line of a fetch file MUST be of the form

    # url length filepath

    # where _url_ identifies the file to be fetched and MUST be an absolute
    # URI as defined in [RFC3986], _length_ is the number of octets in the
    # file (or "-", to leave it unspecified), and _filepath_ identifies the
    # corresponding payload file, relative to the base directory.

    # The slash character ('/') MUST be used as a path separator in
    # _filepath_. One or more linear whitespace characters (spaces or tabs)
    # MUST separate these three values, and any such characters in the
    # _url_ MUST be percent-encoded [RFC3986].  If _filename_ includes an
    # LF, a CR, a CRLF, or a percent sign (%), those characters (and only
    # those) MUST be percent-encoded as described in [RFC3986].  There is
    # no limitation on the length of any of the fields in the fetch file.
    with open(bagit_settings.output_location + "/fetch.txt", 'w') as fetchtxt:
        for f in remote_files :
            fetchtxt.write(f.URI[0] + " - " + f.output_path + "\n")
    pass

def copy_local_files(files) :
    copied_files = []
    try:
        for f in files :
            outdir = bagit_settings.output_location + bagit_settings.prefix
            if f.Subdirectory and len(f.Subdirectory) > 0 :
                outdir = outdir + f.Subdirectory[0]
            os.makedirs(outdir, exist_ok=True)

            copyfile(f.Path[0], bagit_settings.output_location + f.output_path)
            copied_files.append(f.output_path)
        # to copy the files
        pass
    except OSError as e:
        if e.errno == errno.ENOSPC :
            print("Ran out of disk space while copying! Deleting the duplicated files."+
                  "\nPlease make sure you have enough space to make a copy of every file you want to include in the bag.")
        else :
            print(e)
        for f in copied_files :
            os.remove(f)

def create_hash_file(files) :
    with open(bagit_settings.output_location + "manifest-sha512.txt", 'w') as hashfile:
        for f in files :
           f_hash = calculate_sha_512(f.Path[0])
           hashfile.write("%s %s" % (f_hash, f.output_path)) 

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
            v = create_new_bagit_loc(v, "local")
        return values

    @validator('Data')
    @classmethod
    def create_bag_names(cls, values) :
        for dtentry in values :
            if dtentry.Primary:
                for dentry in dtentry.Primary:
                    dentry = create_new_bagit_loc(dentry, "local")
            if dtentry.Copy:
                for dentry in dtentry.Copy:
                    dentry = create_new_bagit_loc(dentry, "local")
            if dtentry.Ref:
                for dentry in dtentry.Ref:
                    dentry = create_new_bagit_loc(dentry, "remote")

        return values
    
    @root_validator
    @classmethod
    def create_list_things_to_copy(cls, values) :
        local = []
        remote = []
        if values.get("File") and len(values.get("File")) > 0 :
            arbfiles = values.get("File")
            for f in arbfiles :
                if f.URI and len(f.URI) > 0 :
                    remote.append(f)
                else : 
                    local.append(f)
        
        for major in ["Data", "Software"] :
            if values.get(major) :
                for maj in values.get(major) :
                    if maj.Ref and len(maj.Ref) > 0 :
                        remote.extend(maj.Ref)
                    if maj.Copy and len(maj.Copy) > 0:
                        local.extend(maj.Copy)
                    if maj.Primary and len(maj.Primary) > 0:
                        local.extend(maj.Primary)

        values["local"] = local
        values["remote"] = remote
        return values

## Runners
def runBagitMode(parameters, medford_input) :
    bagdir = medford_input + "_BAG/"
    if not os.path.isdir(bagdir) :
        os.mkdir(bagdir)
    if not os.path.isdir(bagdir + "data") :
        os.mkdir(bagdir + "data/")
    bagit_settings.output_location = bagdir

    #adjust_mfd_add_to_local(parameters.local)
    copy_local_files(parameters.local)
    create_fetch_txt(parameters.remote)
    create_hash_file(parameters.local)
    #zip_all_files()
