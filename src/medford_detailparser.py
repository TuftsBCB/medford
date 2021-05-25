# Take 3!
from copy import deepcopy
from medford_detail import *

class detailparser :
    data = {}

    def __init__(self, details) :
        self.parse_details(details)

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
                    self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, True)

            elif cur_minor == "desc" :
                self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, True)

            else :
                self.add_to_dict(detail.Major_Tokens, detail.Minor_Token, detail.Data, False)
            prev_minor = cur_minor
            prev_major = cur_major

    def add_to_dict(self, major_list, minor, data, append=False):
        cur_dict = self.data
        for n,major in enumerate(major_list) :
            if major not in cur_dict.keys() :
                cur_dict[major] = [{}]
                cur_dict = cur_dict[major][0]
            else :
                if append == True and n == len(major_list) - 1:
                    cur_dict[major].append({})
                cur_dict = cur_dict[major][-1]
        
        if minor not in cur_dict.keys() :
            cur_dict[minor] = [data]
        else :
            cur_dict[minor].append(data)
                
    def export(self) :
        return deepcopy(self.data)

    