from typing import Dict, List
from .errors import *

class MedfordErrorManager(object):
    _instance = None

    _syntax_err_coll: Dict[int, List[MFDErr]]
    _other_err_coll: Dict[int, List[MFDErr]]
    _pydantic_err_coll: Dict[int, List[MFDErr]]

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
            cls._instance._pydantic_err_coll = {}
            # any initialization goes here
            
        return cls._instance

    def add_error(self, err: MFDErr) :
        if err.errtype == ErrType.SYNTAX :
            self._add_syntax_err(err)
        elif err.errtype == ErrType.PYDANTIC :
            self._add_pydantic_err(err)
        else :
            self._add_other_err(err)
        
        pass
    def _add_syntax_err(self, err: MFDErr) :
        lineno = err.get_head_lineno()
        if lineno in self._syntax_err_coll.keys() :
            self._syntax_err_coll[lineno].append(err)
        else :
            self._syntax_err_coll[lineno] = [err]

    def has_syntax_err(self) :
        return len(self._syntax_err_coll) > 0 
    
    def n_syntax_errs(self) :
        n = 0
        for k,v in self._syntax_err_coll.items() :
            n = n + len(v)
        return n

    def _add_other_err(self, err: MFDErr) :
        lineno = err.get_head_lineno()
        if lineno in self._other_err_coll.keys() :
            self._other_err_coll[lineno].append(err)
        else :
            self._other_err_coll[lineno] = [err]

    def has_other_err(self) :
        return len(self._other_err_coll) > 0
    
    def n_other_errs(self) :
        n = 0
        for k,v in self._other_err_coll.items() :
            n = n + len(v)
        return n
    
    def _add_pydantic_err(self, err: MFDErr) :
        lineno = err.get_head_lineno()
        if lineno in self._pydantic_err_coll.keys() :
            self._pydantic_err_coll[lineno].append(err)
        else :
            self._pydantic_err_coll[lineno] = [err]

    def handle_pydantic_errors(self, errs):
        for e in errs.errors() :
            if e['type'] == "missing" :
                block_info = e['input']['Block']
                missing_token = e['loc'][2]
                # lock = (MAJOR, ?, MINOR) TODO: check in other cases
                self.add_error(MissingRequiredField(block_info, missing_token))
            else :
                raise ValueError("Error manager was passed a pydantic error it does not know how to handle: %s" % str(e))
        pass

    @classmethod
    def _clear_errors(cls) :
        cls._instance = None
        return cls.instance()

