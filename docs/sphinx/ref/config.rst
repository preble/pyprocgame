****************
config Submodule
****************

.. module: procgame.config

The ``config`` submodule serves as a central location for pyprocgame runtime configuration settings.  When this module is loaded the YAML format configuration file located at :file:`~/.pyprocgame/config.yaml` is loaded (if it exists) into :attr:`~procgame.config.values`.  Other modules may then access the data structure either directly or by using the :func:`~procgame.config.value_for_key_path`.

See :ref:`config-yaml` for a complete description of the system configuration file format.


Members
-------

.. autofunction:: procgame.config.value_for_key_path

.. autodata:: procgame.config.values
