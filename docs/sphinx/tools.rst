procgame Tools
==============

About
-----

pyprocgame includes a number of tools to make certain tasks easier, but also as demonstration code.  They are contained in the ``tools`` folder, and should generally be invoked from the main pyprocgame folder::

  python tools/dmdconvert.py ...


dmdconvert.py
-------------

Use :file:`dmdconvert.py` to convert one or more image files into a 16-color ``.dmd`` animation file, which can later be loaded by :meth:`procgame.dmd.Animation.load`.  Its usage is as follows::

  python tools/dmdconvert.py <image1> [... <imageN>] <output.dmd>

If only one image name is supplied, the ``%d`` format specifier may be used to iterate over image files matching a pattern::

  python tools/dmdconvert.py Animation%03d.png Animation.dmd

Additionally, UNIX shells with wildcard expansion support allow the following::

  python tools/dmdconvert.py Animation*.png Animation.dmd

:file:`dmdconvert.py` requires the Python Imaging Library (PIL).  It does not require that the P-ROC hardware be installed.

dmdfontwidths.py
----------------

:file:`dmdfontwidths.py` provides an interactive, text-based interface for specifying the font widths of individual characters in a ``.dmd`` font file.  Its usage is as follows::

  python tools/dmdfontwidths.py <font.dmd> <text>

The provided text will be displayed using the P-ROC hardware in the given font file, which may be a single-frame ``.dmd``; if it is a second frame will be added to contain the font widths (this is a feature of :meth:`procgame.dmd.Font.load`).

To assign character widths, enter the character(s) you wish to change and press return.  Then type the width to assign to all of the specified characters at once.  The DMD will be updated with the new font width values.  Repeat this process until the font widths of the given text are to your liking.  Hit return with a blank line to exit.  

Tips:

* All characters in a new font will have a zero width; as such there will likely be nothing shown on the DMD.  
* Given the limited width of the DMD you will likely need to use several text strings to configure all of the characters in the font.



dmdplayer.py
------------

:file:`dmdplayer.py` displays a ``.dmd`` file on the DMD.  Its usage is as follows::

  python tools/dmdplayer.py <file.dmd>


