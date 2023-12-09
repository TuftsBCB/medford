# Take 3!
from copy import deepcopy
import functools
import math

from pydantic import BaseModel

from MEDFORD.medford_detail import *
from MEDFORD.medford_error_mngr import *

class detailparser :

    def __init__(self, details, err_mngr) :
        self.data = {}
        self.parse_details(details)
        self.err_mngr = err_mngr

    def parse_details(self, details) :
        prev_major = "-1"
        for detail in details :
            cur_minor = detail.Minor_Token
            cur_major = detail.Combined_Major_Token
            if not cur_major == prev_major:
                if not detail.Minor_Token == "desc" :
                    error_mngr.add_syntax_err(mfd_no_desc(detail.Line_Number, cur_major))
                    # Add a dummy desc so we can keep running for now.
                    self.add_to_dict(detail.Major_Tokens, "desc", "NO DESC PROVIDED", detail.Line_Number, False)
                    self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, detail.Line_Number, False)
                else :
                    self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, detail.Line_Number, True)

            elif cur_minor == "desc" :
                self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, detail.Line_Number, True)

            else :
                self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, detail.Line_Number, False)
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

    @staticmethod
    def travel_major_tokens(curdat:BaseModel, current_majors: List[str]) -> List[str] :
        set_attributes = curdat.model_fields_set
        all_keys = list(curdat.model_fields.keys())
        collapsed_majors = '_'.join(current_majors)
        output_strings = []
        
        for attr in set_attributes :
            if attr not in all_keys :
                all_keys.append(attr)

        for attr in all_keys :
            if attr not in curdat.model_fields and curdat.model_extra is not None:
                vals = curdat.model_extra[attr]
            elif curdat.__getattribute__(attr) != None :
                vals = curdat.__getattribute__(attr)
            else : 
                continue
            
            for val in vals :
                val = val[1]
                if issubclass(type(val), BaseModel) :
                    # this is a major token again, so we need to recurse
                    res = detailparser.travel_major_tokens(val, current_majors + [attr])
                    output_strings.extend(res)
                else :
                    # we're in a minor token, so start writing coach
                    if attr != "desc" :
                            output_strings.append(f'@{collapsed_majors}-{attr} {val}\n')
                    else :
                        output_strings.append(f'@{collapsed_majors} {val}\n')
        
        # if we haven't already had a newline, add a newline
        # ( double-newline happens if we're in a multi-major-token that is not followed by a sister major token,
        #   e.g. :
        #   Data-Primary asdf
        #   Software-Primary fdsa
        # 
        #   instead of:
        #   Data-Primary asdf
        #   Data-Ref fdsa)
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
            if len(location_hint_slice) == 0 :
                error_line_number = -1
            else:
                error_line_number = t_err[0]

            ##### RELATED TOKENS #####
            if n_3ples > 0:
                token_indices = list(range(0, (n_3ples)*3,3))
            else :
                token_indices = [0]
            tokens = [error_loc[i] for i in token_indices]
            token_string = "@" + tokens[0]
            if len(tokens) > 1:
                for token in tokens[1:-1]:
                    token_string = token_string + "_" + token
                token_string = token_string + "-" + tokens[-1]

            error_obj = mfd_err(error_line_number, error_type, tokens, error_loc[-1], error_msg)
            self.err_mngr.add_error(error_obj)
        self.err_mngr.print_errors()

    @staticmethod
    def write_from_model(model:BaseModel, location:str) -> None:
        with open(location, 'w') as f:
            lines = detailparser.travel_major_tokens(model, [])
            # Because I wrote it, I know lines is going to end up with an extra newline.
            # Remove it for cleanliness.
            if lines[-1] == "\n" :
                lines = lines[:-1]
                # Again, because I wrote it, I know that every line ends with a newline.
                # Remove the newline from the last line so we don't have a trailing newline.
                lines[-1] = lines[-1][:-1]
            for line in lines :
                f.write(line)
