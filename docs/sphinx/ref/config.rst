****************
config Submodule
****************

.. module: procgame.config

The ``config`` submodule serves as a central location for pyprocgame runtime configuration settings.  When this module is loaded the YAML format configuration file located at :file:`~/.pyprocgame/config.yaml` is loaded (if it exists) into :attr:`~procgame.config.values`.  Other modules may then access the data structure either directly or by using the :func:`~procgame.config.value_for_key_path`.

Example config.yaml
-------------------

The following :file:`config.yaml` demonstrates use of the ``font_path`` key path used by :data:`procgame.dmd.font_path`::

  font_path:
    - .
    - ../shared/dmd

Members
-------

.. autofunction:: procgame.config.value_for_key_path

.. autodata:: procgame.config.values
