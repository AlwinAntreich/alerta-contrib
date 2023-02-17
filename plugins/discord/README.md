Discord Plugin
==================

Post a [Discord](https://discord.com/) message for new alerts.

Installation
------------

Clone the GitHub repo and run:

    $ python setup.py install

Or, to install remotely from GitHub run:

    $ pip install git+https://github.com/alerta/alerta-contrib.git#subdirectory=plugins/discord

Note: If Alerta is installed in a python virtual environment then plugins
need to be installed into the same environment for Alerta to dynamically
discover them.

Configuration
-------------

References
----------

Restart Alerta API and confirm that the plugin has been loaded and enabled.

Set `DEBUG=True` in the `alertad.conf` configuration file and look for log
entries similar to below:

```
2023-02-17 20:13:47,589 alerta.plugins[30]: [DEBUG] Server plugin 'discord' found. [in /venv/lib/python3.8/site-packages/alerta/utils/plugin.py:34]
2023-02-17 20:13:47,762 alerta.plugins[30]: [INFO] Server plugin 'discord' loaded. [in /venv/lib/python3.8/site-packages/alerta/utils/plugin.py:42]
2023-02-17 20:13:47,763 alerta.plugins[30]: [INFO] All server plugins enabled: reject, blackout, normalise, enhance, discord [in /venv/lib/python3.8/site-packages/alerta/utils/plugin.py:45]
```

License
-------

Copyright (c) 2023 Alwin Antreich. Available under the MIT License.
