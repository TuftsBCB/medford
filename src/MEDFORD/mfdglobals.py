from MEDFORD.submodules.mfdvalidator.validator import MedfordValidator as mv

validator: mv
version: str

def init() :
    global validator
    validator = mv.init()

    global version
    version = "2.0"