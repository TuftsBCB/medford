import re, os

def generate_output_name(directory_name, input_file) :
    name = (directory_name if directory_name[-1] == "/" else (directory_name + "/")) + os.path.basename(input_file)
    return name

def valid_filename_bagit(name) :
    valid_filename_pattern = "^[^%\s]+$"
    return not (re.search(valid_filename_pattern, name) is None)

def valid_input_file(filename) :
    can_access = os.access(filename, os.R_OK)
    if not can_access :
        return (False, "Cannot access file: " + filename)
    is_directory = os.path.isdir(filename)
    if is_directory :
        return (False, "File " + filename + " is a directory. MEDFORD does not currently support " + 
                        "copying directories into bagit files.")
    return (True, None)