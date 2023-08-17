from typing import Dict, List
from MEDFORD.submodules.medforderrors.errors import MFDErr

class MedfordErrorManager(object):
    _instance = None

    _syntax_err_coll: Dict[int, List[MFDErr]]
    _other_err_coll: Dict[int, List[MFDErr]]

    # TODO: error options, eg:
    #   - sorting
    #   - fail mode (on first, after collection)
    #   - verbosity (errors, warnings)
    
    @classmethod
    def instance(cls) -> 'MedfordErrorManager':
        if cls._instance is None :
            print('Creating new MedfordErrorManager instance.')
            cls._instance = super(MedfordErrorManager, cls).__new__(cls)

            cls._instance._syntax_err_coll = {}
            cls._instance._other_err_coll = {}
            # any initialization goes here
            
        return cls._instance

    def add_syntax_err(self, err: MFDErr) :
        lineno = err.get_head_lineno()
        if lineno in self._syntax_err_coll.keys() :
            self._syntax_err_coll[lineno].append(err)
        else :
            self._syntax_err_coll[lineno] = [err]

    def add_err(self, err: MFDErr) :
        lineno = err.get_head_lineno()
        if lineno in self._other_err_coll.keys() :
            self._other_err_coll[lineno].append(err)
        else :
            self._other_err_coll[lineno] = [err]

    @classmethod
    def _clear_errors(cls) :
        cls._instance = None
        return cls.instance()

