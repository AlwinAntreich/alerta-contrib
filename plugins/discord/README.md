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

Add `discord` to the list of enabled `PLUGINS` in `alertad.conf` and set
the webhook URL. Each setting can also be given as an environment variable.

```python
PLUGINS = ['reject', 'blackout', 'discord']
DASHBOARD_URL = 'https://alerta.example.com'  # required
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/...'
```

`DISCORD_WEBHOOK_URL` may also be a dictionary that maps an alert's
environment to a webhook, so each environment posts to its own channel:

```python
DISCORD_WEBHOOK_URL = {
    'Production': 'https://discord.com/api/webhooks/...',
    'Infrastructure': 'https://discord.com/api/webhooks/...',
}
```

Optional settings:

| Setting | Default | Description |
|---|---|---|
| `DISCORD_CONTENT` | empty | text posted above the embed |
| `DISCORD_ICON` | Alerta logo | avatar of the message |
| `ALERTA_USERNAME` | `alerta` | name the message is posted as |
| `DISCORD_SHOW_ENVIRONMENT` | `False` | add the alert's environment and customer to the message |

Messages
--------

The plugin posts one message, with the alert text as its description,
when:

* a new alert is received,
* a received alert changes the severity or the status, for example
  critical (open) to cleared (closed),
* someone or something changes the status by an action (ack, shelve,
  close, timeout); the action's text is the description.

Duplicates that change nothing and alerts in a blackout period post no
message.

A message shows the event as its title, the alert or action text, and
one line with the status, the resource and the value:

```
[croit.uptime.croit_container_uptime]
CRITICAL: container uptime (time of last restart)
**Status** Open · **Resource** mgmt · **Value** `00:00:47`
```

With `DISCORD_SHOW_ENVIRONMENT = True`, a second line adds the
environment and, if the alert has one, the customer.

The colour of the message tells the severity:

| Colour | Severity or status |
|---|---|
| red | security, critical, major |
| orange | minor, warning |
| green | cleared, normal, ok |
| blue | status ack, shelved or closed by hand, whatever the severity |
| grey | informational, debug, trace, indeterminate, unknown |

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
