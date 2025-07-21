from MEDFORD.submodules.mfdvalidator.validator import MedfordValidator as mv

validator: mv
version: str


def init():
    global version
    version = "2.0.0"

    global debug
    debug = False

    global validator
    validator = mv.init()
