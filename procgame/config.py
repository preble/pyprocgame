import os
import yaml

values = None
"""Configuration data structure loaded from ~/.pyprocgame/config.yaml."""

def value_for_key_path(keypath):
    """Returns the value at the given keypath within :attr:`values`.  
    A key path is a list of components delimited by dots (periods).  The components are interpreted
    as dictionary keys within the structure.
    For example, the key path 'a.b' would yield 'c' with the following dictionary:
    
        {'a':{'b':'c'}}
    """
    v = values
    for component in keypath.split('.'):
        if v != None and v.has_key(component):
            v = v[component]
        else:
            raise ValueError, 'Key path component %s not found in %s' % (component, v)
    return v

def initialize():
    global values
    path = os.path.expanduser('~/.pyprocgame/config.yaml')
    if not os.path.exists(path):
        return
    print("Loading pyprocgame config from %s..." % path)
    values = yaml.load(open(path, 'r'))

initialize()
