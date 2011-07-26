procgame Command Line Tool
==========================

pyprocgame includes a number of tools to make certain tasks easier.  Your installation should have included a ``procgame`` command line tool.  Once ``procgame`` is in your path (the steps for this will depend on your specific platform; on some platforms it will already be in your path), you can invoke it on the command line::

	$ procgame
	Usage: procgame <command> <arg0> <arg1> ... <argN>

	Commands:
	  config            Configuration tool.
	  dmdconvert        Converts image files to .dmd files.
	  dmdfontwidths     Interactively assign font width values.
	  dmdplayer         Play a .dmd file.
	  dmdsplashrom      Create a P-ROC ROM with a custom power-up image.
	  lampshow          Play a lamp show.

Without any arguments, ``procgame`` shows the available commands within the tool.  Run ``procgame`` again with the command specified in order to see information about that command::

	$ procgame dmdconvert
	Usage: procgame dmdconvert [options] <image1.png> [... <imageN.png>] <output.dmd>
	
	  If only one image name is used it may include %d format specifiers to
	  ...
	  ...

The following documents the specifics of some of the ``procgame`` tools.


.. _tool-config:

config
------

The ``config`` tool assists in managing the pyprocgame configuration file, located at ``~/.pyprocgame/config.yaml``.  Run it without any arguments to see the location of your config.yaml file::

	$ procgame config
	Your configuration file is located at:

	  /home/me/.pyprocgame/config.yaml

You can assign string values in your configuration using the ``--set`` option::

	$ procgame config --key=pinproc_class --set=procgame.fakepinproc.FakePinPROC

Or clear them with ``--clear``::

	$ procgame config --key=pinproc_class --clear

You can also use ``config`` to manage your ``font_path``::

	$ procgame config --key=font_path --add="/home/me/dmd_fonts"

Run ``procgame config --help`` to view other options.


.. _tool-dmdconvert:

dmdconvert
----------

Use ``dmdconvert`` to convert one or more image files into a 16-color ``.dmd`` animation file, which can later be loaded by :meth:`procgame.dmd.Animation.load`.  Its usage is as follows::

  procgame dmdconvert <image1> [... <imageN>] <output.dmd>

If only one image name is supplied, the ``%d`` format specifier may be used to iterate over image files matching a pattern::

  procgame dmdconvert Animation%03d.png Animation.dmd

Additionally, UNIX shells with wildcard expansion support allow the following::

  procgame dmdconvert Animation*.png Animation.dmd

``dmdconvert`` requires the Python Imaging Library (PIL).  It does not require that the P-ROC hardware be installed.


dmdfontwidths
-------------

``dmdfontwidths`` provides an interactive, text-based interface for specifying the font widths of individual characters in a ``.dmd`` font file.  Its usage is as follows::

  procgame dmdfontwidths <font.dmd> <text>

The provided text will be displayed using the P-ROC hardware in the given font file, which may be a single-frame ``.dmd``; if it is a second frame will be added to contain the font widths (this is a feature of :meth:`procgame.dmd.Font.load`).

To assign character widths, enter the character(s) you wish to change and press return.  Then type the width to assign to all of the specified characters at once.  The DMD will be updated with the new font width values.  Repeat this process until the font widths of the given text are to your liking.  Hit return with a blank line to exit.  

Tips:

* All characters in a new font will have a zero width; as such there will likely be nothing shown on the DMD.  
* Given the limited width of the DMD you will likely need to use several text strings to configure all of the characters in the font.


dmdplayer
---------

``dmdplayer`` displays a ``.dmd`` file on the DMD.  Its usage is as follows::

  procgame dmdplayer <file.dmd>


.. _tool-dmdsplashrom:

dmdsplashrom
------------

``dmdsplashrom`` requests a new P-ROC ROM image (.p-roc file) with a custom power-up image.  Usage::

  procgame dmdsplashrom <key> <base_fpga_version> <file.dmd> <output.p-roc>

``key``
	A transaction key obtained from support@pinballcontrollers.com.

``base_fpga_version``
	Version number of the desired base P-ROC image.  Format is x.yy (ie: 1.18).

``file.dmd``
	Splash screen image in the .dmd format - must be a single frame at 128x32.

``output.p-roc``
	Filename for the new P-ROC image.  Must end in ".p-roc".

All images made with this utility will have a P-ROC watermark applied, showing 'P-ROC' and the image version number.
