# Take 3!
from copy import deepcopy
from medford_detail import *

class detailparser :

    def __init__(self, details) :
        self.data = {}
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
            
    def recursive_write_from_dict(f, keystring, curdict, newline = False) :
        for idx, tag in enumerate(curdict.keys()) :
            if curdict[tag] is not None :
                if isinstance(curdict[tag], list) :
                    for dat in curdict[tag] :
                        if isinstance(dat, dict):
                            if keystring == "" :
                                detailparser.recursive_write_from_dict(f, tag, dat)
                            else :
                                detailparser.recursive_write_from_dict(f, keystring + "_" + tag, dat)
                        else :
                            if keystring == "" :
                                f.write("@" + tag + " " + str(dat) + "\n")
                            else :
                                if tag != "desc" :
                                    f.write("@" + keystring + "-" + tag + " " + str(dat) + "\n")
                                else :
                                    f.write("@" + keystring + " " + str(dat) + "\n")
                else :
                    dat = curdict[tag]
                    if tag != "desc" :
                        f.write("@" + keystring + "-" + tag + " " + str(dat) + "\n")
                    else :
                        f.write("@" + keystring + " " + str(dat) + "\n")
                if newline :
                    f.write("\n")

    def write_from_dict(d, location):
        with open(location, 'w') as f:
            detailparser.recursive_write_from_dict(f, "", d, newline = True)