import logging
import os
import requests

try:
    from alerta.plugins import app  # alerta >= 5.0
except ImportError:
    from alerta.app import app  # alerta < 5.0
from alerta.plugins import PluginBase

LOG = logging.getLogger('alerta.plugins.discord')

DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL') or app.config['DISCORD_WEBHOOK_URL']
DISCORD_CONTENT     = os.environ.get('DISCORD_CONTENT') or app.config.get('DISCORD_CONTENT', '')
DISCORD_ICON        = os.environ.get('DISCORD_ICON') or app.config.get('DISCORD_ICON', 'https://raw.githubusercontent.com/alerta/alerta-webui/master/public/favicon-128.png')
DASHBOARD_URL       = os.environ.get('DASHBOARD_URL') or app.config['DASHBOARD_URL']
ALERTA_USERNAME     = os.environ.get('ALERTA_USERNAME') or app.config.get('ALERTA_USERNAME', 'alerta')

# discord wants decimals instead of hex
DEFAULT_SEVERITY_MAP = {
    'security': '0',  # black
    'critical': '16711680',  # red
    'major': '16753920',  # orange
    'minor': '16776960',  # yellow
    'warning': '16753920',  # orange
    'informational': '8421504',  #gray
    'debug': '8421504',  # gray
    'trace': '8421504',  # gray
    'cleared': '52224',  # green
    'ok': '52224'  # green
    }


class PostMessage(PluginBase):

    def pre_receive(self, alert):
        return alert

    def post_receive(self, alert):
        if alert.repeat:
            return
        self._post_message(self._prepare_payload(alert))

    def status_change(self, alert, status, text):
#        if status not in ['ack', 'assign']:
#            return
        self._post_message(self._prepare_payload(alert, status, text))

    @staticmethod
    def _prepare_payload(alert, status=None, text=None):
        LOG.debug('Discord: %s, %s, %s', alert, status, text)

        color = DEFAULT_SEVERITY_MAP.get(alert.severity) or DEFAULT_SEVERITY_MAP.get('informational')

        title = '[{event}]'.format(event=alert.event)

        status = (status if status else alert.status).capitalize()

        return {
                "avatar_url": DISCORD_ICON,
                "content": DISCORD_CONTENT,
                "username": ALERTA_USERNAME,
                "embeds": [{
                    "url": DASHBOARD_URL,
                    "title": title,
                    "description": text,
                    "color": color,
                    "fields": [
                        {
                            "name": "Status",
                            "value": status,
                            "inline": True
                        },
                        {
                            "name": "Serverity",
                            "value": alert.severity.capitalize() or '',
                            "inline": True
                        },
                        {
                            "name": "Value",
                            "value": alert.value or '',
                        },
                        {
                            "name": "Resource",
                            "value": alert.resource or '',
                        },
                        {
                            "name": "Environment",
                            "value": alert.environment or '',
                            "inline": True
                        },
                        {
                            "name": "Customer",
                            "value": alert.customer or 'None',
                            "inline": True
                        }
                    ],
                    }],
                }

    @staticmethod
    def _post_message(payload):
        LOG.debug('Discord: %s', payload)

        try:
            r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=2)
        except Exception as e:
            raise RuntimeError("Discord: ERROR - %s" % e)

        LOG.debug('Discord: %s - %s', r.status_code, r.text)
