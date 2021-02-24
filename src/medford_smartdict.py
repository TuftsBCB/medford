from copy import deepcopy
class SmartDict:
    # Private
    def __init__(self, keylist) :
        self._coredict = {'desc': []} # Modified using add method; obtained using export
        for key in keylist:
            if key not in self._coredict.keys() :
                self._coredict[key] = []
    
    def addFromToken(self, token) :
        newkey = token.get_major()
        data = token.get_body()
        self.add(newkey, data)

    def add(self, newkey, data) :
        if newkey not in self._coredict.keys() :
            raise ValueError("SmartDict given key not provided during initialization: " + str(newkey))
        
        self._coredict[newkey].append(data)
    
    def export(self) :
        return deepcopy(self._coredict)
    
    def __str__(self) :
        return(self._coredict.__str__())