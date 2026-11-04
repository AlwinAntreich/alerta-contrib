import logging
import os
import requests
from flask import g

try:
    from alerta.plugins import app  # alerta >= 5.0
except ImportError:
    from alerta.app import app  # alerta < 5.0
from alerta.plugins import PluginBase

LOG = logging.getLogger('alerta.plugins.discord')

DISCORD_WEBHOOK_URL = os.environ.get(
    'DISCORD_WEBHOOK_URL') or app.config.get('DISCORD_WEBHOOK_URL')
DISCORD_CONTENT = os.environ.get(
    'DISCORD_CONTENT') or app.config.get('DISCORD_CONTENT', '')
DISCORD_ICON = os.environ.get('DISCORD_ICON') or app.config.get(
    'DISCORD_ICON',
    'https://raw.githubusercontent.com/alerta/alerta-webui/master/public/favicon-128.png')
DASHBOARD_URL = os.environ.get('DASHBOARD_URL') or app.config['DASHBOARD_URL']
ALERTA_USERNAME = os.environ.get(
    'ALERTA_USERNAME') or app.config.get('ALERTA_USERNAME', 'alerta')

# discord wants decimals instead of hex
DEFAULT_SEVERITY_MAP = {
    'security': '0',  # black
    'critical': '16711680',  # red
    'major': '16753920',  # orange
    'minor': '16776960',  # yellow
    'warning': '16753920',  # orange
    'informational': '8421504',  # gray
    'debug': '8421504',  # gray
    'trace': '8421504',  # gray
    'cleared': '52224',  # green
    'ok': '52224'  # green
}


class PostMessage(PluginBase):
    # One message per received alert that is new, changes severity or changes
    # status, and one per status change made by an action (ack, close, ...).
    #
    # While an alert is received, Alerta calls status_change() with the
    # stored alert (old severity and value) before post_receive() gets the
    # updated one. status_change() then only records the change, and
    # post_receive() posts it with the current data.

    def pre_receive(self, alert):
        g.discord_receiving = True
        g.discord_status_changed = False
        return alert

    def post_receive(self, alert):
        g.discord_receiving = False
        status_changed = g.pop('discord_status_changed', False)

        # don't let us repeat ourselves or
        # send messages if a blackout period is set
        if (alert.repeat and not status_changed) or alert.status == 'blackout':
            return

        url = self._get_environment(alert)
        self._post_message(self._prepare_payload(alert, text=alert.text), url)

    def status_change(self, alert, status, text):
        # don't send messages if a blackout period is set
        if status == 'blackout':
            return

        # post_receive() sends it with the updated alert
        if g.get('discord_receiving'):
            g.discord_status_changed = True
            return

        url = self._get_environment(alert)
        self._post_message(self._prepare_payload(alert, status, text), url)

    @staticmethod
    def _get_environment(alert):
        url = DISCORD_WEBHOOK_URL
        if isinstance(DISCORD_WEBHOOK_URL, dict):
            url = DISCORD_WEBHOOK_URL.get(alert.environment)

        return url

    @staticmethod
    def _prepare_payload(alert, status=None, text=None):
        LOG.debug('Discord: %s, %s, %s', alert, status, text)

        color = DEFAULT_SEVERITY_MAP.get(
            alert.severity) or DEFAULT_SEVERITY_MAP.get('informational')

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
                        "name": "Severity",
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
    def _post_message(payload, url):
        LOG.debug('Discord: %s', payload)

        try:
            r = requests.post(url, json=payload, timeout=2)
        except Exception as e:
            raise RuntimeError("Discord: ERROR - %s" % e)

        LOG.debug('Discord: %s - %s', r.status_code, r.text)
