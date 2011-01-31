Installation
============

Prerequisites
-------------

Before you install pyprocgame, you will need the following software components:

* `Python 2.6 <http://python.org/>`_
* `pypinproc <http://github.com/preble/pypinproc>`_ -- native Python extension enabling P-ROC hardware control.  Exposes the `libpinproc <http://github.com/preble/libpinproc>`_ API to Python and adds native DMD frame manipulation features.  See the :ref:`branch note <pyprocgame-branch>` below.
* `setuptools <http://pypi.python.org/pypi/setuptools>`_ -- required for procgame script installation.  Also adds easy_install, a helpful installer tool for popular Python modules.
* `pyyaml <http://pyyaml.org/>`_ -- YAML parsing.
* One of the Python graphics and sound modules:

  * `pyglet <http://www.pyglet.org/>`_
  * `pygame <http://www.pygame.org/>`_

* `Python Imaging Library <http://www.pythonware.com/products/pil/>`_ (PIL)

Download pyprocgame
-------------------

Download the pyprocgame source code from http://github.com/preble/pyprocgame.

.. _pyprocgame-branch:

.. note:: 
	*Which branch should I download?*
	The two main branches of pyprocgame are master and dev.  Master is the stable branch and is recommended for most users.  New features are first made available in the dev branch, but bugs are much more likely to be found in the dev branch.  Whichever branch you select, **make sure that libpinproc, pypinproc, and pyprocgame are all from the same branch**!


Installing pyprocgame
---------------------

Using the command prompt, change to the pyprocgame directory and install pyprocgame with the following command: (depending on your system configuration you may need to use ``sudo``) ::

	python setup.py install

This will install pyprocgame such that you can import it from any Python script on your system::

	import procgame.game

It will also install the "procgame" command line tool into a system-dependent location.  On Linux and Mac OS X systems this will probably be in your path such that you can type, from the command line::

	procgame

and see a list of available commands.  If it is not in your path you can invoke it directly, or modify your PATH environment variable.  Note that on Windows the procgame script is typically located in C:\\Python26\\Scripts.

.. note::
	If you need to modify the pyprocgame source code (most users will not need to do this) you can use the setup.py script to configure pyprocgame to be "installed" at its present location.  This allows you use pyprocgame as described above without modifying your Python path, etc.  Simply run ``python setup.py develop``.  You can reverse this command with ``python setup.py develop --uninstall``.  Note that this requires the :mod:`setuptools` module to be installed.


.. _config-yaml:

System Configuration File
-------------------------

pyprocgame does not require configuration, but a system configuration file can be used to establish settings specific to your development environment.  Note that this is distinct from the machine configuration file, which configures pyprocgame for the hardware elements of the pinball machine.

The system configuration file is located at :file:`~/.pyprocgame/config.yaml`.  It is in the `YAML file format <http://yaml.org/>`_, a human-friendly file format.

.. note::
	On UNIX-like platforms the ``~`` (tilde) is shorthand for the user's home directory.  Windows does not understand this shorthand, so if you do not know your home directory, run ``procgame config`` to find your configuration file path.

Any plain text editor can be used to edit the system configuration file, or you can use the ``procgame`` tool.  See :ref:`procgame config <tool-config>` for more information.

The system configuration values are processed and accessed by the :mod:`procgame.config` module.

Configuration Keys/Values
^^^^^^^^^^^^^^^^^^^^^^^^^

+--------------------------+----------+----------------------------------------------------+
| Top Level Key            | Type     | Description                                        |
+==========================+==========+====================================================+
| ``config_path``          | Sequence | List of paths that will be searched for machine    |
|                          |          | configuration files via                            |
|                          |          | :meth:`~procgame.game.GameController.load_config`. |
+--------------------------+----------+----------------------------------------------------+
| ``desktop_dmd_scale``    | Number   | (pyglet :class:`~procgame.desktop.Desktop` only)   |
|                          |          | Sets the scale factor of the desktop DMD display.  |
+--------------------------+----------+----------------------------------------------------+
| ``dmd_cache_path``       | String   | Provide a path to the directory to store cached    |
|                          |          | animations in.  If this key is not present, no     |
|                          |          | images will be cached.  See                        |
|                          |          | :meth:`procgame.dmd.Animation.load` for further    |
|                          |          | details.                                           |
+--------------------------+----------+----------------------------------------------------+
| ``font_path``            | Sequence | List of paths that will be searched by             |
|                          |          | :meth:`procgame.dmd.font_named`.                   |
+--------------------------+----------+----------------------------------------------------+
| ``keyboard_switch_map``  | Mapping  | Maps characters (keys) to switches (values); used  |
|                          |          | by :class:`~procgame.desktop.Desktop` to interpret |
|                          |          | keypresses as switch events.  Switch values are    |
|                          |          | run through :meth:`pinproc.decode`.                |
+--------------------------+----------+----------------------------------------------------+
| ``pinproc_class``        | String   | Full name of a class to use as a standin for the   |
|                          |          | :class:`~pinproc.PinPROC` class.  Typically used   |
|                          |          | with :class:`procgame.fakepinproc.FakePinPROC`.    |
+--------------------------+----------+----------------------------------------------------+


Example Configuration
^^^^^^^^^^^^^^^^^^^^^

::

	font_path:
	    - .
	    - ~/Projects/PROC/shared/dmd
	pinproc_class: procgame.fakepinproc.FakePinPROC
	config_path:
	    - ~/Projects/PROC/shared/config
	keyboard_switch_map:
	    # Enter, Up, Down, Exit
	    7: SD8
	    8: SD7
	    9: SD6
	    0: SD5
	    # Start:
	    s: S13
	    z: SF4
	    /: SF2
	desktop_dmd_scale: 2
	dmd_cache_path: ~/.pyprocgame/dmd_cache
