from MEDFORD.submodules.mfdvalidator.validator import MedfordValidator as mv

validator: mv
version: str
debug: bool

# TODO : awkward race conditions between initializing mfdglobals and 
#   medfordvalidator in test cases. reorganize this at some point
def init() :
    global version
    version = "2.0.0"

    global debug
    debug = False

    global validator
    validator = mv.init(debug)