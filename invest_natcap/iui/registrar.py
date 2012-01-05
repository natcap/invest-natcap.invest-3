
class Registrar(object):
    def __init__(self):
        object.__init__(self)
        self.map = {}
        
    def update_map(self, updates):
        self.map.update(updates)
        
    def eval(self, mapKey, opValues):
        return self.map[mapKey](opValues)
    
    def get_func(self, mapKey):
        return self.map[mapKey]
    
    def is_key_in_map(self, mapKey):
        return mapKey in self.map
    
class DatatypeRegistrar(Registrar):
    def __init__(self):
        Registrar.__init__(self)
        
        updates = {'int': int,
                   'float': float}
        self.update_map(updates)
        
    def eval(self, mapKey, opValues):
        if is_key_in_map():
            return Registrar.eval(mapKey, opValues)
        else:
            return str(opValues)
        