import procgame
import os
import sys
import yaml

def save_config():
    try:
        output = file(procgame.config.path, 'w')
        yaml.dump(procgame.config.values, output)
        del output
    except IOError:
        print("Error writing to configuration file at "+procgame.config.path)
        sys.exit(2)

def tool_populate_options(parser):
    parser.add_option('-k', '--key', action='store', help='The configuration key to be manipulated.')
    parser.add_option('-a', '--add', action='store', help='Add VALUE to list KEY.', metavar='VALUE')
    parser.add_option('-r', '--remove', action='store', help='Remove VALUE from list KEY.', metavar='VALUE')

def tool_get_usage():
    return """[options]"""

def tool_run(options, args):
    no_values_loaded = (procgame.config.values == {})
    procgame.config.values = procgame.config.values or {}
    if options.key:
        if options.key not in procgame.config.values and not options.add:
            print("Key does not exist.")
            sys.exit(3)

        if options.add or options.remove:
            if options.key in procgame.config.values and type(procgame.config.values[options.key]) != list:
                print("Cannot add or remove values from a key that does not have a list value.  Type is "+(type(procgame.config.values[options.key]).__name__))
                sys.exit(3)
            
            if options.add:
                if options.key not in procgame.config.values:
                    procgame.config.values[options.key] = []
                procgame.config.values[options.key].append(options.add)
                save_config()
                return True
            if options.remove:
                procgame.config.values[options.key].remove(options.remove)
                save_config()
                return True
        
        print procgame.config.values[options.key]
        return True
    
    # If nothing else, show the file location and some diagnostic information:
    print("""Your configuration file is located at:""")
    print("")
    print("""  %s""" % (procgame.config.path))
    print("")
    
    if not os.path.exists(procgame.config.path):
        print 'Your configuration file does not exist.'
    elif no_values_loaded:
        print 'Your configuration file contains one or more errors and was not parsed successfully.'
    
    return True
