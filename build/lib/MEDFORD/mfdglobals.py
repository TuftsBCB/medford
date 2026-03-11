from .submodules.mfdvalidator.validator import MedfordValidator as mv
from pathlib import Path

validator: mv
version: str
debug: bool


def init():

    global version
    version = "2.0.0"

    global debug
    debug = False

    global validator
    validator = mv.init(validator_file)

    global validator_file
    package_dir = Path(__file__).parent
    validator_file = package_dir / "medford.mvd"

def ForceNewValidator() :
    global validator
    validator = mv.init(validator_file)
