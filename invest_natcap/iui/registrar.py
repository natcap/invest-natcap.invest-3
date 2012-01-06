
class Registrar(object):
    def __init__(self):
        object.__init__(self)
        self.map = {}
        
    def update_map(self, updates):
        self.map.update(updates)
        
    def eval(self, mapKey, opValues):
        try:
            return self.map[mapKey](opValues)
        except KeyError: #key not in self.map
            return None
    
    def get_func(self, mapKey):
        return self.map[mapKey]
    
class DatatypeRegistrar(Registrar):
    def __init__(self):
        Registrar.__init__(self)
        
        updates = {'int': int,
                   'float': float}
        self.update_map(updates)
        
    def eval(self, mapKey, opValues):
        cast_value = Registrar.eval(mapKey, opValues)

        if cast_value == None:
            return str(opValues)

        return cast_value
