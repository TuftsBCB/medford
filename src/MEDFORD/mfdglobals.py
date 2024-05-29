from submodules.medforderrors.errormanager import MedfordErrorManager as em

validator: em
version: str

def init() :
    global validator
    validator = em.init()

    global version
    version = "2.0"