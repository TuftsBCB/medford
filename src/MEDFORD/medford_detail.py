from os import major
import re
from typing import List, Tuple, Union

from MEDFORD.medford_error_mngr import error_mngr, mfd_duplicated_macro, mfd_remaining_template, mfd_unexpected_macro, mfd_no_desc, mfd_wrong_macro_token, mfd_empty_line

class detail_return():
    type: str
    is_novel : bool = False
    detail : 'detail' = None
    macro : Tuple[str, Tuple[int, str]] = None

    def __init__(self, type, is_novel, detail, macro):
        self.type = type
        if type == "detail_return" :
            self.is_novel = is_novel
            self.detail = detail
        elif type == "macro_return" :
            self.macro = macro
        else : 
            raise Exception("Unexpected behavior in detail.FromLine. Attempted to create detail_return with type '{}'".format(type))

class detail() :
    #static
    template_flag = "[..]"
    macro_head = "`@"
    macro_flag = "`@"
    macro_regex = "({}\{{[a-zA-Z0-9_]+\}}|{}[a-zA-Z0-9]+\s)".format(macro_flag, macro_flag)

    comment_head = "#"
    comment_flag = "# "
    detail_head = "@"

    macro_dictionary = {}
    named_dictionary = {} # collection of named major tokens

    #instance
    Major_Tokens = []
    Combined_Major_Token = ""
    Minor_Token = ""
    Line_Number = -1
    Depth = -1
    Data = ""

    def __init__(self, majors, minor, lineno, depth, data):
        self.Major_Tokens = majors
        self.Combined_Major_Token = '_'.join(majors)
        self.Minor_Token = minor
        self.Line_Number = lineno
        self.Depth = depth
        self.Data = data

    @classmethod
    def _clear_cache(cls) :
        detail.macro_dictionary = {}

    @classmethod
    def _validate_comment(cls, **params) :
        pass

    @classmethod
    def _remove_inline_comment(cls, line:str) :
        if detail.comment_flag in line:
            return line.split(detail.comment_flag)[0].strip()

    @classmethod
    def _validate_noncomment(cls, line:str, lineno:int, previous_return: Union[None, detail_return, str], err_mngr:error_mngr) :
        if detail.template_flag in line:
            err_mngr.add_syntax_err(mfd_remaining_template(lineno))

    @classmethod
    def _handle_macro_definition(cls, line:str, lineno:int, err_mngr:error_mngr) :
        head = line[0:len(detail.macro_flag)]
        if head[0] == " " or head[0] == "\t" :
            # raise a warning to the user telling them to not put spaces directly after macro head.
            pass # for now
        
        macro_name, macro_body = line.split(" ",1)
    
        if macro_name in detail.macro_dictionary.keys() :
            old_lineno = detail.macro_dictionary[macro_name][0]
            err_mngr.add_syntax_err(mfd_duplicated_macro(lineno, old_lineno, macro_name))
        
        # If this is duplicated, we're not going to finish parsing anyways. 
        # Just set the macro value to be the new value for now.
        macro_data = (lineno, macro_body)
        detail.macro_dictionary[macro_name] = macro_data
        return detail_return('macro_return', None, None, (macro_name, macro_data))

    @classmethod
    def _substitute_macro(cls, data:str, lineno:int, err_mngr:error_mngr) :
        curled_macro_regex = "{}\{{[a-zA-Z0-9_]+\}}".format(detail.macro_flag)
        if re.search(curled_macro_regex, data) :
            # we've found a macro that's curled
            macro_loc = re.search(curled_macro_regex, data).span()
            macro_fullname = data[macro_loc[0]:macro_loc[1]] # includes macro head and curly brackets

            macro_name_start = macro_loc[0] + len(detail.macro_flag) + 1 # +1 because of curly bracket
            macro_name_end = macro_loc[1] - 1 # -1 because of curly bracket
            found_macro_name = data[macro_name_start:macro_name_end]
        else :
            # we've found a macro that's not curled
            macro_loc = re.search("{}[a-zA-Z0-9_]\w+".format(detail.macro_flag), data).span() # TODO : check that this works too :clown:
            macro_fullname = data[macro_loc[0]:macro_loc[1]] # includes macro head

            macro_name_start = macro_loc[0] + len(detail.macro_head) # has to move head pointer b/c of macro
            macro_name_end = macro_loc[1]
            found_macro_name = data[macro_name_start:macro_name_end]
            
        if found_macro_name in detail.macro_dictionary.keys() :
            data = data.replace(macro_fullname, detail.macro_dictionary[found_macro_name][1])
        else :
            err_mngr.add_syntax_err(mfd_unexpected_macro(lineno, found_macro_name))
        return data

    @classmethod
    def _bool_defines_macro(cls, line:str) -> bool:
        if line[0:2] == detail.macro_head :
            return True
        else :
            return False

    @classmethod
    def _bool_contains_macro(cls, line:str) -> bool:
        if re.search(detail.macro_regex, line):
            return True
        else :
            return False
        
    @classmethod
    def _get_Major_Minor_Body(cls, line:str) -> Tuple[List[str], str, int, str]:
        tokens, body = str.split(line, " ", 1)

        # remove leading @
        tokens = tokens[1:]
        tokens_list = tokens.split("-")
        major_tokens = tokens_list[0].split("_")

        # if there are no minor tokens, tokens_list is [majors]
        if len(tokens_list) == 1 :
            minor_token = "desc"
        else :
            minor_token = tokens_list[1]
        
        depth = len(tokens_list)

        return(major_tokens, minor_token, depth, body)
    
    @classmethod
    def FromLine(cls, line: str, lineno: int, previous_return: Union[None, detail_return], err_mngr: error_mngr) -> Union[None, detail_return] :
        # TODO: breaking this up into smaller pieces.
        """Generate a Detail object from a line, the line number, and the Detail generated directly previous.

        :param line: A string to parse into a detail, from a MFD file.
        :type line: str
        :param lineno: The line number in the MFD file that 'line' came from.
        :type lineno: int
        :param prev_detail: The previous detail generated from this MEDFORD file, if applicable.
        :type prev_detail: Detail|None
        :raises ValueError: A Template marker ("[..]") is observed in the provided line.
        :raises MedfordFormatException: A Macro name that has already been used is detected.
        :raises MedfordFormatException: A Macro is referred to that has not yet been defined.
        :raises ValueError: A catch-all error when we have no idea how to process the line provided.
        :return: A 3-tuple describing : Is this detail data, is this NOVEL detail data, and the Detail object. The 'novel' data flag was added to accomodate multi-line details.
        :rtype: Tuple(Bool, Bool, Detail)
        """
        line = line.strip()
        comment_removed = False
        
        # Line contains a comment
        if detail.comment_flag in line :
            line = detail._remove_inline_comment(line)
            comment_removed = True

        # Line is empty
        if(len(line) == 0) :
            if previous_return is not None :
                previous_return.is_novel = False
            return previous_return
        
        # Line IS a comment
        if(line[:len(detail.comment_head)] == detail.comment_head) :
            if previous_return is not None :
                previous_return.is_novel = False
            return previous_return

        # Generic validation for anything that isn't a comment; raises if something is wrong
        # but otherwise continues.
        #   (e.g. a template marker is still present)
        detail._validate_noncomment(line, lineno, previous_return, err_mngr)

        # Line is defining a macro
        if line[:len(detail.macro_head)] == detail.macro_head :
            return detail._handle_macro_definition(line, lineno, err_mngr)

        elif line[:len(detail.macro_head)] == "'@" :
            err_mngr.add_syntax_err(mfd_wrong_macro_token(lineno)) 
            # If they tried & failed to define a macro, should reset previous return.
            return None

        # Line follows the standard major-minor format
        elif line[0] == "@" :
            if len(str.split(line, " ")) == 1 :
                err_mngr.add_syntax_err(mfd_empty_line(lineno, comment_removed, str.split(line, " ")[0]))
                return previous_return
            
            major_tokens, minor_token, depth, body = cls._get_Major_Minor_Body(line)

            if minor_token != "desc":
                if previous_return is None or not previous_return.type == "detail_return" :
                    err_mngr.add_syntax_err(mfd_no_desc(lineno, major_tokens + [minor_token]))
                elif not previous_return.detail.Major_Tokens == major_tokens :
                    err_mngr.add_syntax_err(mfd_no_desc(lineno, major_tokens + [minor_token]))

            if detail.macro_flag in body :
                body = detail._substitute_macro(body, lineno, err_mngr)

            return detail_return("detail_return", True, cls(major_tokens, minor_token, lineno, depth, body), None)

        # Line is a run-over from a previous line.
        else :
            if previous_return is None :
                raise Exception("Unhandled previous_return type: NoneType in detail.FromLine. %d %s" % (lineno, line))

            if previous_return.type == "detail_return" :
                if detail.macro_flag in line :
                    line = detail._substitute_macro(line, lineno, err_mngr)
                    
                previous_return.detail.addData(line)
                return detail_return("detail_return", False, previous_return.detail, None)

            elif previous_return.type == "macro_return" :
                detail.addMacroData(previous_return, line)
                # Not technically necessary -- can just return previous return.
                #   changing it though to make it match the detail_return case for legibility
                return detail_return("macro_return", None, None, previous_return.macro)

            else :
                # I think this will only occur if someone basically just starts typing in an empty file, with no
                #   macro or major-minor tokens?
                raise Exception("Unhandled previous_return type: " + str(previous_return.type) + " in detail.FromLine")
                #err_mngr.add_major_parsing_error(lineno, "formatting", f"Line " + str(lineno) + \
                #    " does not lead with a @ or a # (has neither a token nor is a comment.) " + \
                #    "Did you forget to declare a token? Or did you mean to make this a comment?")


    # TODO: add logic to check if next line leads with space or not.
    def addData(self, line) :
        self.Data = self.Data + " " + line
    
    @classmethod
    def addMacroData(cls, macro_return, line) :
        macro_name = macro_return.macro[0]
        old_entry = detail.macro_dictionary[macro_name]
        detail.macro_dictionary[macro_name] = (old_entry[0], old_entry[1] + " " + line)

    @classmethod
    def _find_named(cls, line) -> Tuple[bool, Union[str, None], Union[str, None]] :
        if '@' in line :
            major_tokens, minor_token, _, body = cls._get_Major_Minor_Body(line)
            # !!WARNING!! Will not work if there is a macro in the body!!
            # SPEC UPDATE NEEDED: Should this behave well with a macro?
            #                       (personally, I think yes, b/c what if 50+ samples, can re-use prefix as macro)
            if minor_token == "desc" :
                return (True, "-".join(major_tokens), body)
            else :
                return(False, None, None)
        return (False, None, None)

    @classmethod
    def readDetails(cls, filename, err_mngr) :
        details = []
        all_lines = []
        with open(filename, 'r') as f:
            all_lines = f.readlines()
        
        for i, line in enumerate(all_lines) :
            has_named, major, name = cls._find_named(line)
            if has_named :
                if major not in cls.named_dictionary.keys() :
                    cls.named_dictionary[major] = [name]
                else :
                    cls.named_dictionary[major].append(name)

        dr = None
        for i, line in enumerate(all_lines):
            if(line.strip() != "") :
                dr = detail.FromLine(line, i+1, dr, err_mngr)
                if isinstance(dr, detail_return) :
                    if dr.is_novel :
                        details.append(dr.detail)
    
        if err_mngr.has_major_parsing :
            return (True, details, err_mngr.return_syntax_errors())

        return (False, details, None)

    def tabstring(self) :
        if self.Minor_Token != 'desc' :
            return('\t'*self.depth + self.Minor_Token + ': ' + self.Data)
        else :
            return(self.Minor_Token + ': ' + self.Data)
