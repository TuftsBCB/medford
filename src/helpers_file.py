import re, os
import urllib3

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
