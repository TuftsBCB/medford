from copy import deepcopy
from typing import List


#TODO: Check how much everything breaks if I try to sort by token on pre-processing errors.

class mfd_syntax_err(SyntaxError):
    lineno:int
    errtype:str
    inst_terminal:bool
    late_terminal:bool

    # adding the late_terminal flag to mark whether or not the parser should stop before reaching pydantic.
    # this may be not necessary, but it will be easier to refactor to remove it later than to refactor to add it.
    def __init__(self, message:str, lineno:int, errtype:str, inst_terminal:bool, late_terminal:bool):
        super().__init__(message)
        self.lineno = lineno
        self.errtype = errtype
        self.inst_terminal = inst_terminal
        self.late_terminal = late_terminal

    def __str__(self):
        return f"{self.errtype} on line {self.lineno}: {self.args[0]}"

class mfd_unexpected_macro(mfd_syntax_err):
    def __init__(self, lineno:int, macro_name:str) :
        self.substr = macro_name
        message = f"Unexpected macro '{macro_name}' on line {lineno}."
        super().__init__(message, lineno, "unexpected_macro", False, True)

    def duplicate(self) :
        return mfd_unexpected_macro(self.lineno, self.substr)

class mfd_duplicated_macro(mfd_syntax_err):
    def __init__(self, instance_1:int, instance_2:int, macro_name:str) :
        self.substr = macro_name
        self.earlier_lineno = instance_1
        message = f"Duplicated macro '{macro_name}' on lines {instance_1} and {instance_2}."
        super().__init__(message, instance_2, "duplicated_macro", False, True)
    
    def duplicate(self) :
        return mfd_duplicated_macro(self.earlier_lineno, self.lineno, self.substr)

class mfd_remaining_template(mfd_syntax_err):
    def __init__(self, lineno:int):
        message = f"Remaining template marker on line {lineno}."
        super().__init__(message, lineno, "remaining_template", False, True)

    def duplicate(self) :
        return mfd_remaining_template(self.lineno)

class mfd_no_desc(mfd_syntax_err):
    def __init__(self, lineno:int, major_token:str):
        self.substr = major_token
        message = f"Novel token @{major_token} started without a description on line {lineno}."
        super().__init__(message, lineno, "no_desc", False, True)
    
    def duplicate(self) :
        return mfd_no_desc(self.lineno, self.substr)

class mfd_wrong_macro_token(mfd_syntax_err) :
    def __init__(self, lineno:int) :
        message = f"Wrong token used to define a macro on line {lineno}. Please use `@, not '@, when defining a macro."
        super().__init__(message, lineno, "wrong_macro_token", False, True)

    def duplicate(self) :
        return mfd_wrong_macro_token(self.lineno)

class mfd_empty_line(mfd_syntax_err) :
    def __init__(self, lineno:int, has_comment, rest_of_line) :
        self.has_comment = has_comment
        self.substr = rest_of_line
        message = f"No content provided on line {lineno}, only tokens: {self.substr}."
        if has_comment :
            message = message + " An inline comment was found on this line -- did you mean to make it a comment?"
        super().__init__(message, lineno, "empty_line", False, True)

    def duplicate(self) :
        return mfd_empty_line(self.lineno, self.has_comment, self.substr)
class mfd_err:
    def __init__(self, line: int, errtype: str, token_context: List[str],
                token_name: str, msg: str) :
        self.line = line
        self.errtype = errtype

        if self.errtype != "macro_misuse" :
            self.token_context = token_context
            token_string = "@" + token_context[0]
            if len(token_context) > 1:
                for token in token_context[1:-1]:
                    token_string = token_string + "_" + token
                token_string = token_string + "-" + token_context[-1]
            self.token_string = token_string

            self.token_name = token_name
        else :
            self.token_string = "NA"
            self.token_name = "NA"

        self.msg = msg

    def __str__(self) :
        self.lineno = self.line
        if self.errtype == "missing_field" :
            return f"Line {self.lineno: <10} : {self.token_string} is missing the field {self.token_name}."
        elif self.errtype == "incomplete_data" :
            return f"Line {self.lineno: <10} : {self.token_string} has incomplete information: {self.msg}."
        elif self.errtype == "macro_misuse" :
            return f"Line {self.lineno: <10} : {self.msg}"
        else:
            return f"Line {self.lineno: <10} : {self.token_string} is of the wrong type: {self.msg}."

class error_mngr:
    has_major_parsing = False
    # mode : ("ALL", "FIRST")
    # order: ("TYPE", "TOKENS", "LINE")
    def __init__(self, mode, order):
        self._syntax_err_coll = {}
        self._error_collection = {}
        self.has_major_parsing = False
        self.mode = mode
        self.order = order

    def add_syntax_err(self, err_obj:mfd_syntax_err):
        if err_obj.late_terminal :
            self.has_major_parsing = True
        if err_obj.inst_terminal :
            raise err_obj
        # TODO: Add ordering functionality, for now I'm just assuming lineno ordering
        if err_obj.lineno not in self._syntax_err_coll.keys() :
            self._syntax_err_coll[err_obj.lineno] = [err_obj]
        else :
            self._syntax_err_coll[err_obj.lineno].append(err_obj)

    def print_syntax_errors(self):
        print("\nSyntax errors:")
        for line in sorted(self._syntax_err_coll.keys()) :
            for err in self._syntax_err_coll[line] :
                print("\t" + str(err))

    def add_error(self, error_obj: mfd_err):
        if self.mode == "FIRST" :
            print("Stopping on first error: ")
            print("\t" + str(error_obj))
            raise SystemExit(0)

        if self.order == "TYPE" :
            keyval = error_obj.errtype
        elif self.order == "TOKENS" :
            keyval = error_obj.token_string
        elif self.order == "LINE" :
            keyval = error_obj.line

        if keyval not in self._error_collection.keys() :
            self._error_collection[keyval] = [error_obj]
        else :
            self._error_collection[keyval].append(error_obj)

    def return_errors(self): 
        return deepcopy(self._error_collection)

    def return_syntax_errors(self) :
        output_dict = {}
        for key in self._syntax_err_coll :
            output_dict[key] = list(map(lambda err: err.duplicate(), self._syntax_err_coll[key]))

        return output_dict

    def print_errors(self):
        if self.order == "TYPE" :
            title = "Errors of type "
        elif self.order == "TOKENS" :
            title = "Errors on token "
        elif self.order == "LINE" :
            title = "Errors on line "

        for keyval in self._error_collection.keys() :
            if self.order != "LINE" :
                print(title + str(keyval) + ": ")
            for err in self._error_collection[keyval] :
                print("\t" + str(err))