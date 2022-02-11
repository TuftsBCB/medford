from typing import List
class mfd_err:
    def __init__(self, line: int, errtype: str, token_context: List[str],
                token_name: str, msg: str) :
        self.line = line
        self.errtype = errtype

        self.token_context = token_context
        token_string = "@" + token_context[0]
        if len(token_context) > 1:
            for token in token_context[1:-1]:
                token_string = token_string + "_" + token
            token_string = token_string + "-" + token_context[-1]
        self.token_string = token_string

        self.token_name = token_name
        self.msg = msg

    def __str__(self) :
        if self.errtype == "missing_field" :
            return f"Line {self.line: <10} : {self.token_string} is missing the field {self.token_name}."
        elif self.errtype == "incomplete_data" :
            return f"Line {self.line: <10} : {self.token_string} has incomplete information: {self.msg}."
        else:
            return f"Line {self.line: <10} : {self.token_string} is of the wrong type: {self.msg}."

class error_mngr:
    def __init__(self, mode="ALL", order="LINE"):
        self._error_collection = {}
        self.mode = mode
        self.order = order

    def add_error(self, error_obj: mfd_err):
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

    def print_errors(self):
        if self.order == "TYPE" :
            title = "Errors of type "
        elif self.order == "TOKENS" :
            title = "Errors on token "
        elif self.order == "LINE" :
            title = "Errors on line "

        for keyval in self._error_collection.keys() :
            print(title + str(keyval) + ": ")
            for err in self._error_collection[keyval] :
                print("\t" + str(err))
