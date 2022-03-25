# Take 3!
from copy import deepcopy
import functools
import math

from pydantic import BaseModel

from medford_detail import *
from medford_error_mngr import *

class detailparser :

    def __init__(self, details, err_mngr) :
        self.data = {}
        self.parse_details(details)
        self.err_mngr = err_mngr

    def parse_details(self, details) :
        prev_minor = "-1"
        prev_major = "-1"
        for detail in details :
            cur_minor = detail.Minor_Token
            cur_major = detail.Combined_Major_Token
            if not cur_major == prev_major:
                if not detail.Minor_Token == "desc" :
                    raise ValueError("Error: Tried to describe new data without starting with a description line on line " + str(detail.Line_Number) + \
                            "\nBefore this line, there should be a line like this: @"+ detail.Combined_Major_Token + " [A DESCRIPTION HERE]")
                else :
                    self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, detail.Line_Number, True)

            elif cur_minor == "desc" :
                self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, detail.Line_Number, True)

            else :
                self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, detail.Line_Number, False)
            prev_minor = cur_minor
            prev_major = cur_major

    def add_to_dict(self, major_list, minor, data, lineno, append=False):
        cur_dict = self.data
        for n,major in enumerate(major_list) :
            if major not in cur_dict.keys() :
                cur_dict[major] = [(lineno, {})]
                cur_dict = cur_dict[major][0][1]
            else :
                if append == True and n == len(major_list) - 1:
                    cur_dict[major].append((lineno, {}))
                cur_dict = cur_dict[major][-1][1]

        if minor not in cur_dict.keys() :
            cur_dict[minor] = [(lineno, data)]
        else :
            cur_dict[minor].append((lineno, data))

    def export(self) :
        return deepcopy(self.data)

    def recursive_write(self, f, keystring, curdict) :
        for idx, tag in enumerate(curdict.keys()) :
            for dat in curdict[tag] :
                if isinstance(dat, dict) :
                    if keystring != "" :
                        self.recursive_write(f, keystring + "_" + tag, dat)
                    else :
                        self.recursive_write(f, tag, dat)
                else :
                    if keystring == "" :
                        f.write("@" + tag + " " + dat + "\n")
                    else :
                        f.write("@" + keystring + "-" + tag + " " + dat + "\n")
                    if(idx == len(curdict.keys()) - 1) :
                        f.write("\n")

    def write(self, location) :
        with open(location, 'w') as f:
            self.recursive_write(f, "", self.data)

    def travel_major_tokens(curdat:BaseModel, current_majors: List[str]) -> List[str] :
        set_attributes = curdat.__fields_set__
        all_keys = list(curdat.__fields__.keys())
        collapsed_majors = '_'.join(current_majors)
        output_strings = []
        
        for attr in set_attributes :
            if attr not in all_keys :
                all_keys.append(attr)

        for attr in all_keys :
            if curdat.__getattribute__(attr) != None :
                for val in curdat.__getattribute__(attr) :
                    val = val[1]
                    if issubclass(type(val), BaseModel) :
                        # this is a major token again, so we need to recurse
                        res = detailparser.travel_major_tokens(val, current_majors + [attr])
                        output_strings.extend(res)
                    else :
                        if attr != "desc" :
                                output_strings.append(f'@{collapsed_majors}-{attr} {val}\n')
                        else :
                            output_strings.append(f'@{collapsed_majors} {val}\n')
        
        if output_strings[-1] != "\n" :
            output_strings.append("\n")
        return output_strings

    def parse_pydantic_errors(self, errs, dict) :
        errors = errs.errors()
        ## first, compress all related errors
        error_locations = {}
        for e in errors:
            if e['loc'] not in error_locations.keys() :
                error_locations[e['loc']] = [e]
            else :
                error_locations[e['loc']].append(e)

        for error_loc in error_locations.keys() :
            error_type = None
            current_errors = error_locations[error_loc]
            # are all of these just the result of there being multiple valid types, and none of them were found?
            if len(current_errors) > 1 :
                all_type_errors = functools.reduce(lambda a, b: a and ("value_error" in b['type']) and (not "missing" in b['type']), current_errors)
                if all_type_errors == True :
                    # FOR NOW just take the first one
                    error_msg = current_errors[0]['msg']
                    error_type = "value_error"
                else :
                    raise NotImplementedError("Multiple error types have been raised at the same location. Check this out!")
            else :
                if "missing" in current_errors[0]['type'] :
                    error_type = "missing_field"
                elif "incomplete_data_error" in current_errors[0]['type']:
                    error_type = "incomplete_data"
                elif "value_error" in current_errors[0]['type'] :
                    error_type = "value_error"
                elif "type_error" in current_errors[0]['type'] :
                    error_type = "value_error" # hurts to type, but...
                error_msg = current_errors[0]['msg']

            # Below this, we assume that we only care about the first error.

            ##### LINE NUMBER #####
            # Get the index in pydantic's 'loc' n-ple that corresponds to the line number of the most specific relevant block.
            n_3ples = math.floor(len(error_loc)/3.0)
            start_last3 = (n_3ples-1)*3
            end_last3 = (n_3ples)*3
            location_hint_slice = error_loc[:(end_last3-1)]

            # Get the line number that index points to.
            t_err = dict
            for location_hint in location_hint_slice :
                t_err = t_err[location_hint]
            error_line_number = t_err[0]

            ##### RELATED TOKENS #####
            token_indices = list(range(0, (n_3ples)*3,3))
            tokens = [error_loc[i] for i in token_indices]
            token_string = "@" + tokens[0]
            if len(tokens) > 1:
                for token in tokens[1:-1]:
                    token_string = token_string + "_" + token
                token_string = token_string + "-" + tokens[-1]

            error_obj = mfd_err(error_line_number, error_type, tokens, error_loc[-1], error_msg)
            self.err_mngr.add_error(error_obj)
        self.err_mngr.print_errors()


    def write_from_model(model:BaseModel, location:str) -> None:
        with open(location, 'w') as f:
            lines = detailparser.travel_major_tokens(model, [])
            if lines[-1] == "\n" :
                lines = lines[:-1]
                lines[-1] = lines[-1][:-1]
            for line in lines :
                f.write(line)
