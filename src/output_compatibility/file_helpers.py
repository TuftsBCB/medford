import re, os
from src.output_compatibility.bagit_helpers import bagit_settings

def generate_output_name(directory_name, input_file) :
    name = (directory_name if directory_name[-1] == "/" else (directory_name + "/")) + os.path.basename(input_file)
    return name

def valid_filename_bagit(name) :
    is_valid = not ((re.search(bagit_settings.regex, name)) is None)
    reason = ""
    if not is_valid :
        reason = "Output filename " + name + " is invalid. Output filenames cannot contain whitespaces or the '%' symbol."
    return (is_valid, reason)

def valid_input_file(filename) :
    can_access = os.access(filename, os.R_OK)
    if not can_access :
        return (False, "Cannot access file: " + filename)
    is_directory = os.path.isdir(filename)
    if is_directory :
        return (False, "File " + filename + " is a directory. MEDFORD does not currently support " + 
                        "copying directories into bagit files.")
    return (True, None)

def swap_file_loc(file_obj) :
    # TODO: Find a way that doesn't delete all other parameters.
    new_obj = {'desc': file_obj.desc, 'Path': [file_obj.NewName]}
    return new_obj

def create_new_bagit_loc(FileObj) :
    output_name = bagit_settings.prefix + generate_output_name(FileObj.Subdirectory[0], FileObj.Path[0])
    can_write_new, reason = valid_filename_bagit(output_name)
    if not can_write_new:
        raise ValueError("Cannot copy file, reason: " + reason)
    can_read_old, reason = valid_input_file(FileObj.Path[0])
    if not can_read_old :
        raise ValueError("Cannot copy file, reason: " + reason)
    FileObj.NewName = output_name
    return FileObj