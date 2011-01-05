"""Configuration tool."""
import procgame
import os
import sys

def tool_populate_options(parser):
    pass

def tool_get_usage():
    return """[options]"""

def tool_run(options, args):
    # If nothing else, show the file location:
    print """Your configuration file is located at:

  %s
""" % (procgame.config.path)
    
    if not os.path.exists(procgame.config.path):
        print 'Your configuration file does not exist.'
    elif procgame.config.values == None:
        print 'Your configuration file contains one or more errors and was not parsed successfully.'
    
    return True
