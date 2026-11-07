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
DISCORD_SHOW_ENVIRONMENT = True if os.environ.get(
    'DISCORD_SHOW_ENVIRONMENT', 'False') == 'True' else app.config.get(
    'DISCORD_SHOW_ENVIRONMENT', False)

# discord wants decimals instead of hex; one colour per level of urgency
DEFAULT_SEVERITY_MAP = {
    'security': '15548997',  # red
    'critical': '15548997',  # red
    'major': '15548997',  # red
    'minor': '15761935',  # orange
    'warning': '15761935',  # orange
    'indeterminate': '9807270',  # grey
    'informational': '9807270',  # grey
    'debug': '9807270',  # grey
    'trace': '9807270',  # grey
    'unknown': '9807270',  # grey
    'cleared': '3908956',  # green
    'normal': '3908956',  # green
    'ok': '3908956'  # green
}

# a person acted on the alert: these statuses are blue, whatever the
# severity, unless the alert is cleared (green)
STATUS_COLOR_MAP = {
    'ack': '3447003',  # blue
    'shelved': '3447003',  # blue
    'closed': '3447003',  # blue, closed by hand
}

MARKDOWN_CHARS = '\\*_~|`'


def _escape(value):
    # keep alert data from being read as Discord markdown
    return ''.join('\\' + c if c in MARKDOWN_CHARS else c for c in value or '')


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

        status = status if status else alert.status

        color = DEFAULT_SEVERITY_MAP.get(
            alert.severity) or DEFAULT_SEVERITY_MAP.get('informational')
        if status in STATUS_COLOR_MAP and color != DEFAULT_SEVERITY_MAP['ok']:
            color = STATUS_COLOR_MAP[status]

        title = '[{event}]'.format(event=alert.event)

        facts = ['**Status** ' + status.capitalize(),
                 '**Resource** ' + _escape(alert.resource)]
        if alert.value:
            facts.append('**Value** `{}`'.format(alert.value.replace('`', "'")))
        lines = [_escape(text)] if text else []
        lines.append(' · '.join(facts))

        if DISCORD_SHOW_ENVIRONMENT:
            location = ['**Environment** ' + _escape(alert.environment)]
            if alert.customer:
                location.append('**Customer** ' + _escape(alert.customer))
            lines.append(' · '.join(location))

        return {
            "avatar_url": DISCORD_ICON,
            "content": DISCORD_CONTENT,
            "username": ALERTA_USERNAME,
            "embeds": [{
                "url": DASHBOARD_URL,
                "title": title,
                "description": '\n'.join(lines),
                "color": color,
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
