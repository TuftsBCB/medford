import re, os
import urllib3
from helpers_bagit import bagit_settings

def generate_output_name(directory_name, input_file) :
    """
    Create output file name

    Given a directory name and an input filename, combines them into one final
    name. This automatically ensures that they are separated by a "/", even if
    the directory name does not contain it.

    Both directory_name and input_file are expected to be non-null.
    """
    name = (directory_name if directory_name[-1] == "/" else (directory_name + "/")) + os.path.basename(input_file)
    return name

def valid_filename_bagit(name) :
    """
    Validates input filename against bagit requirements
    """
    is_valid = not ((re.search(bagit_settings.regex, name)) is None)
    reason = ""
    if not is_valid :
        reason = "Output filename " + name + " is invalid. Output filenames cannot contain whitespaces or the '%' symbol."
    return (is_valid, reason)

def valid_input_file(filename) :
    """
    Validates that the given fine is a. accessible and b. not a directory.
    """
    can_access = os.access(filename, os.R_OK)
    if not can_access :
        return (False, "Cannot access file: " + filename)
    is_directory = os.path.isdir(filename)
    if is_directory :
        return (False, "File " + filename + " is a directory. MEDFORD does not currently support " + 
                        "copying directories into bagit files.")
    return (True, None)

def swap_file_loc(file_obj) :
    """
    Adjusts a given File object such that its Path is the location it was set to be copied to.

    Requires that a File has gone to a create_new_*_loc function, such that its NewName parameter is defined.
    """
    new_obj = file_obj
    new_obj.Path = new_obj.bagName
    new_obj.pop('bagName', None)
    new_obj.pop('Subdirectory', None)
    return new_obj

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
        http = urllib3.PoolManager()
        filename = os.path.basename(FileObj.URI[0])
        request = http.request('GET', FileObj.URI[0])
        if (request.status != 200) :
            raise ValueError("Cannot reach file...")
        with open(filename, "wb") as f:
            f.write(request.data)
        # Strip out to just the name of the file
        # Then generate output name and continue as expected
        FileObj.Path = [filename]

    if FileObj.Subdirectory :
        output_name = bagit_settings.prefix + generate_output_name(FileObj.Subdirectory[0], FileObj.Path[0])
    else :
        output_name = bagit_settings.prefix + "/" + FileObj.Path[0]
    
    can_write_new, reason = valid_filename_bagit(output_name)
    if not can_write_new:
        raise ValueError("Cannot copy file, reason: " + reason)
    can_read_old, reason = valid_input_file(FileObj.Path[0])
    if not can_read_old :
        raise ValueError("Cannot copy file, reason: " + reason)
    FileObj.bagName = output_name
    return FileObj