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

class detail() :
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
    def FromLine(cls, line, lineno, prev_detail) :
        line = line.strip()
        if(line[0] == "#") :
            return (False, False, None)
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

            return (True, True, cls(major_tokens, minor_token, lineno, depth, data))
        else :
            if prev_detail is None:
                raise ValueError("ERROR: Line " + str(lineno) + \
                    " does not lead with a @ or a # (has neither a token nor is a comment.) " + \
                    "Did you forget to declare a token? Or did you mean to make this a comment?\n\tLINE: " + line)
            return(True, False, prev_detail.addData(line))


    def addData(self, line) :
        self.Data = self.Data + " " + line
    
    def tabstring(self) :
        if self.Minor_Token != 'desc' :
            return('\t'*self.depth + self.Minor_Token + ': ' + self.Data)
        else :
            return(self.Minor_Token + ': ' + self.Data)