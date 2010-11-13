import os
import yaml

values = None
"""The configuration data structure loaded from :file:`~/.pyprocgame/config.yaml` when this submodule is loaded."""

def value_for_key_path(keypath, default=None):
    """Returns the value at the given *keypath* within :attr:`values`.
    
    A key path is a list of components delimited by dots (periods).  The components are interpreted
    as dictionary keys within the structure.
    For example, the key path ``'a.b'`` would yield ``'c'`` with the following :attr:`values` dictionary: ::
    
        {'a':{'b':'c'}}
    
    If the key path does not exist *default* will be returned.
    """
    v = values
    for component in keypath.split('.'):
        if v != None and v.has_key(component):
            v = v[component]
        else:
            v = default
    return v

def initialize():
    global values
    path = os.path.expanduser('~/.pyprocgame/config.yaml')
    if not os.path.exists(path):
        return
    print("Loading pyprocgame config from %s..." % path)
    values = yaml.load(open(path, 'r'))

initialize()
