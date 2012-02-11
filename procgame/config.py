import os
import yaml
import logging

values = None
"""The configuration data structure loaded from :file:`~/.pyprocgame/config.yaml` when this submodule is loaded."""

path = None
"""Path that the configuration data structure was loaded from, by :meth:`load`."""

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

def load():
    global values, path
    logger = logging.getLogger('game.config')
    curr_path = os.path.expanduser('./config.yaml')
    system_path = os.path.expanduser('~/.pyprocgame/config.yaml')
    if os.path.exists(curr_path):
         path = curr_path
    else:
        logger.warning('pyprocgame configuration not found at %s. Checking %s.' % (curr_path, system_path))
        if os.path.exists(system_path):
            path = system_path
        else:
            logger.warning('pyprocgame configuration not found at %s' % system_path)
            return
    logger.info('pyprocgame configuration found at %s' % path)
    try:
        values = yaml.load(open(path, 'r'))
    except yaml.scanner.ScannerError, e:
        logger.error('Error loading pyprocgame config from %s; your configuration file has a syntax error in it!\nDetails: %s', path, e)
    except Exception, e:
        logger.error('Error loading pyprocgame config from %s: %s', path, e)

load()
