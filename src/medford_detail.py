# Attempting a different structure for tokens that is more straightforward.
# Key parts:
#   A list of all Major tokens (A major token being defined as not a minor token)
#       There must be at LEAST 1 Major token.
#   A Minor token (A minor token being defined as the final token in the list
#                   of tokens for an instance)
#       There must be EXACTLY 1 Minor token.
#   A Line Number (the original line the instance was created from)
#   A Depth (the number of Major tokens in the instance)
#   Data    (the data stored within the instance)

from typing import Union

from medford_error_mngr import error_mngr

class detail_return():
    is_novel : bool = False
    detail : 'detail' = None

    def __init__(self, is_novel, detail):
        self.is_novel = is_novel
        self.detail = detail

class detail() :
    #static
    template_flag = "[...]"
    macro_head = "`@"
    macro_flag = "`@"
    comment_head = "#"
    comment_flag = "# "
    detail_head = "@"

    macro_dictionary = {}

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

    #TODO : For the love of all that is good in this world, split this up into different cases...
    #           e.g. "handle_macro"?
    @classmethod
    def FromLine(cls, line: str, lineno: int, previous_return: Union[None, detail_return, str], err_mngr: error_mngr) -> Union[None, detail_return, str] :
        """Generate a Detail object from a line, the line number, and the Detail generated directly previous.

        :param line: A string to parse into a detail, from a MFD file.
        :type line: str
        :param lineno: The line number in the MFD file that 'line' came from.
        :type lineno: int
        :param prev_detail: The previous detail generated from this MEDFORD file, if applicable.
        :type prev_detail: Detail|None
        :raises ValueError: A Template marker ("[...]") is observed in the provided line.
        :raises MedfordFormatException: A Macro name that has already been used is detected.
        :raises MedfordFormatException: A Macro is referred to that has not yet been defined.
        :raises ValueError: A catch-all error when we have no idea how to process the line provided.
        :return: A 3-tuple describing : Is this detail data, is this NOVEL detail data, and the Detail object. The 'novel' data flag was added to accomodate multi-line details.
        :rtype: Tuple(Bool, Bool, Detail)
        """
        line = line.strip()

        # Line contains a template marker, and isn't a comment
        if line[0] != detail.comment_head :
            if detail.template_flag in line :
                #TODO: Not actually major. Make this throw later.
                err_mngr.add_major_parsing_error("ERROR: Line " + str(lineno) + \
                    " contains the template marker [...]. Please substitute this with actual data!" + \
                    "\n\tLINE: " + line)

        # Line contains a comment
        if detail.comment_flag in line :
            comment_ind = line.find(detail.comment_flag) 
            line = line[:comment_ind]

            # Make sure there's no trailing spaces after we remove the inline comment.
            line = line.strip()

        if(len(line) == 0) :
            return None
        
        # Line IS a comment
        if(line[0] == detail.comment_head) :
            return None

        # TODO: Check that they aren't trying to use '@ to define/use a macro.
        
        # Line is defining a macro
        elif line[:2] == detail.macro_head :
            # TODO: Check that they haven't put an extra space between `@ and the macro name
            macro_name, macro_body = line[2:].split(" ",1)
            if macro_name in detail.macro_dictionary.keys() :
                err_mngr.add_major_parsing_error(lineno, "macro_misuse", f"Line " + str(lineno) + " tries to define macro " + macro_name + " to be '" + 
                    macro_body + "', but " + macro_name + " is already defined!")
            detail.macro_dictionary[macro_name] = macro_body
            return macro_name

        # Line follows the standard major-minor format
        elif line[0] == "@" :
            tokens, body = str.split(line, " ", 1)
            tokens = str.replace(tokens, '@', "")
            tokens_list = tokens.split("-")

            if len(tokens_list) == 1 :
                minor_token = "desc"
            else :
                minor_token = tokens_list[1]
            depth = len(tokens_list)
            major_tokens = tokens_list[0].split("_")
            data = body

            if detail.macro_flag in data :
                # TODO: adjust so I don't need so many magic integers
                first_ind = data.find(detail.macro_flag)
                is_curled = (data[first_ind+2] == "{")
                if is_curled :
                    whitespace_after = first_ind + data[first_ind:].find("}") +1
                    found_macro_name = data[first_ind+3:whitespace_after-1]
                else :
                    whitespace_after = data.find(" ", first_ind)
                    if whitespace_after == -1 :
                        whitespace_after = len(data)

                    found_macro_name = data[first_ind+2:whitespace_after]

                if found_macro_name in detail.macro_dictionary.keys() :
                    data = data[:first_ind] + detail.macro_dictionary[found_macro_name] + data[whitespace_after:]
                else :
                    err_mngr.add_major_parsing_error(lineno, "macro_misuse", f"Line " + str(lineno) + " tries to use macro " + found_macro_name + 
                        ", but this macro has not previously been defined. Are you sure you did not misspell the intended macro name?")

            return detail_return(True, cls(major_tokens, minor_token, lineno, depth, data))

        # Line is a run-over from a previous line.
        else :
            if isinstance(previous_return, detail_return) :
                previous_return.detail.addData(line)
                return detail_return(False, previous_return.detail)
            elif isinstance(previous_return, str) :
                detail.addMacroData(str(previous_return), line)
                return previous_return
            else :
                err_mngr.add_major_parsing_error(lineno, "formatting", f"Line " + str(lineno) + \
                    " does not lead with a @ or a # (has neither a token nor is a comment.) " + \
                    "Did you forget to declare a token? Or did you mean to make this a comment?")


    # TODO: add logic to check if next line leads with space or not.
    def addData(self, line) :
        self.Data = self.Data + " " + line
    
    @classmethod
    def addMacroData(cls, macro_name, line) :
        detail.macro_dictionary[macro_name] = detail.macro_dictionary[macro_name] + " " + line

    def tabstring(self) :
        if self.Minor_Token != 'desc' :
            return('\t'*self.depth + self.Minor_Token + ': ' + self.Data)
        else :
            return(self.Minor_Token + ': ' + self.Data)