## pyprocgame

pyprocgame is a high-level pinball development framework for use with P-ROC (Pinball Remote Operations Controller).  It was written by Adam Preble and Gerry Stellenberg.  More information about P-ROC is available at [pinballcontrollers.com](http://pinballcontrollers.com/).  See the [pyprocgame site](http://pyprocgame.pindev.org/) for the full pyprocgame documentation.

## Prerequisites

pyprocgame requires the following:

- [Python 2.6](http://python.org/)
- [pypinproc](http://github.com/preble/pypinproc) -- native Python extension enabling P-ROC hardware access and native DMD frame manipulation.
- [setuptools](http://pypi.python.org/pypi/setuptools) -- required for procgame script installation.  Also adds easy\_install, a helpful installer tool for popular Python modules.
- [pyyaml](http://pyyaml.org/) -- YAML parsing.
- One of the Python graphics and sound modules:
  - [pyglet](http://www.pyglet.org/)
  - [pygame](http://www.pygame.org/)
- [Python Imaging Library](http://www.pythonware.com/products/pil/) (PIL)

## Installation

To install pyprocgame: (depending on your system configuration you may need to use _sudo_)

	python setup.py install

This will install pyprocgame such that you can import it from any Python script on your system:

	import procgame.game

It will also install the "procgame" command line tool into a system-dependent location.  On Linux and Mac OS X systems this will probably be in your path such that you can type, from the command line:

	procgame

and see a list of available commands.  If it is not in your path you can invoke it directly, or modify your PATH environment variable.  Note that on Windows the procgame script is typically located in C:\Python26\Scripts.

## Documentation

Please see the [pyprocgame Documentation](http://pyprocgame.pindev.org/) site for the pyprocgame Manual and detailed API documentation.

## License

Copyright (c) 2009-2011 Adam Preble and Gerry Stellenberg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.