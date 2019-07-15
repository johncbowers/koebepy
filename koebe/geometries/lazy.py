# From here: http://code.activestate.com/recipes/576720-lazy-property/

def lazyproperty(func):
    """A decorator for lazy evaluation of properties
    """
    cache = {}
    def _get(self):
        try:
            return cache[self]
        except KeyError:
            cache[self] = value = func(self)
            return value
        
    return property(_get)