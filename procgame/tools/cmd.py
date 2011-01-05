import optparse
import os
import sys
import procgame

def main():
    """Command line main for 'procgame'.
    
    To create a command, it must reside in this module and have the following
    methods:
    
        tool_get_usage()
        tool_populate_options(parser)
        tool_run(options, args)
    
    """
    
    # Assemble a list of available commands.
    commands = {}
    for name in dir(procgame.tools):
        module = getattr(procgame.tools, name)
        if hasattr(module, 'tool_run'):
            commands[name] = module
    
    show_help = False
    
    if len(sys.argv) <= 1:
        show_help = True
    elif not sys.argv[1] in commands:
        show_help = True
    
    if show_help:
        print("""Usage: %s <command> <arg0> <arg1> ... <argN>""" % (os.path.basename(sys.argv[0])))
        print("")
        print("Commands:")
        for name in sorted(commands.keys()):
            print """  % -12s  %s""" % (name, commands[name].__doc__)
        sys.exit(1)
    
    command_name = sys.argv[1]
    module = commands[command_name]
    
    parser = optparse.OptionParser()
    parser.usage = """%s %s %s""" % (os.path.basename(sys.argv[0]), sys.argv[1], module.tool_get_usage())
    module.tool_populate_options(parser)
    
    (options, args) = parser.parse_args(sys.argv[2:])
    
    ok = module.tool_run(options, args)
    if not ok:
        parser.print_help()
        sys.exit(1)
    
    
