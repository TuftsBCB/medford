from copy import deepcopy
class SmartDict:
    # Private

    def __init__(self, keylist) :
        self._keys_to_isList = {'desc': False} # Set during initialization
        self._coredict = {} # Modified using add method; obtained using export
        for key in keylist:
            if key in self._keys_to_isList.keys() :
                self._keys_to_isList[key] = True
            else :
                self._keys_to_isList[key] = False
        for key in self._keys_to_isList :
            if self._keys_to_isList[key] :
                # If it's a list, we have to initialize it so we can use
                #       .append() later without having to worry about
                #       initializing it later. Otherwise, we don't care. :)
                self._coredict[key] = []
    
    def addFromToken(self, token) :
        newkey = token.get_major()
        data = token.get_body()
        self.add(newkey, data)

    def add(self, newkey, data) :
        if not newkey in self._keys_to_isList.keys() :
            raise ValueError("SmartDict given key not provided during initialization: " + str(newkey))
        
        if self._keys_to_isList[newkey] :
            self._coredict[newkey].append(data)
        else :
            self._coredict[newkey] = data
    
    def export(self) :
        return deepcopy(self._coredict)
    
    def __str__(self) :
        return(self._coredict.__str__())