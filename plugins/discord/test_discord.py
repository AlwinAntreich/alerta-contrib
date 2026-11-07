import json
import os
import unittest
import uuid
from unittest import mock

from alerta.app import create_app, plugins

WEBHOOK_URL = 'https://discord.com/api/webhooks/0000/XXXX'

RED, ORANGE, GREEN, BLUE = '15548997', '15761935', '3908956', '3447003'


class DiscordPluginTestCase(unittest.TestCase):

    def setUp(self):
        os.environ['DISCORD_WEBHOOK_URL'] = WEBHOOK_URL
        os.environ['DASHBOARD_URL'] = 'https://alerta.example.com'
        self.app = create_app({
            'TESTING': True,
            'AUTH_REQUIRED': False,
        })
        self.client = self.app.test_client()

        # the plugin reads its configuration on import, after create_app()
        import alerta_discord
        plugins.plugins['discord'] = alerta_discord.PostMessage()

        patcher = mock.patch('alerta_discord.requests.post')
        self.post = patcher.start()
        self.addCleanup(patcher.stop)

        self.resource = 'mgmt-' + uuid.uuid4().hex[:8]

    def tearDown(self):
        os.environ.pop('DISCORD_WEBHOOK_URL', None)
        os.environ.pop('DASHBOARD_URL', None)

    def _send(self, severity, text, value):
        alert = {
            'event': 'croit_container_uptime',
            'resource': self.resource,
            'environment': 'Production',
            'service': ['croit'],
            'severity': severity,
            'text': text,
            'value': value,
        }
        response = self.client.post(
            '/alert', data=json.dumps(alert),
            headers={'Content-type': 'application/json'})
        self.assertEqual(response.status_code, 201)
        return json.loads(response.data.decode('utf-8'))['id']

    def _action(self, alert_id, action, text):
        response = self.client.put(
            f'/alert/{alert_id}/action',
            data=json.dumps({'action': action, 'text': text}),
            headers={'Content-type': 'application/json'})
        self.assertEqual(response.status_code, 200)

    def _messages(self):
        messages = []
        for call in self.post.call_args_list:
            embed = call.kwargs['json']['embeds'][0]
            self.assertNotIn('fields', embed)
            messages.append((embed['color'], embed['description']))
        return messages

    def _desc(self, text, status, value, extra=''):
        return (f'{text}\n**Status** {status} · **Resource** {self.resource}'
                f' · **Value** `{value}`{extra}')

    def test_one_message_per_open_and_close(self):
        # A correlated severity change used to post twice: once from
        # status_change with the stored (stale) alert and the new text, and
        # once from post_receive with the new alert and no text.
        self._send('critical', 'CRITICAL: container uptime', '00:00:47')
        self._send('cleared', 'CLEARED: container uptime', '00:05:47')
        self._send('critical', 'CRITICAL: container uptime', '00:00:12')

        self.assertEqual(self._messages(), [
            (RED, self._desc('CRITICAL: container uptime', 'Open', '00:00:47')),
            (GREEN, self._desc('CLEARED: container uptime', 'Closed', '00:05:47')),
            (RED, self._desc('CRITICAL: container uptime', 'Open', '00:00:12')),
        ])

    def test_escalation_posts_once(self):
        self._send('warning', 'WARNING: container uptime', '00:10:00')
        self._send('critical', 'CRITICAL: container uptime', '00:00:47')

        self.assertEqual(self._messages(), [
            (ORANGE, self._desc('WARNING: container uptime', 'Open', '00:10:00')),
            (RED, self._desc('CRITICAL: container uptime', 'Open', '00:00:47')),
        ])

    def test_duplicate_does_not_post(self):
        self._send('critical', 'CRITICAL: container uptime', '00:00:47')
        self._send('critical', 'CRITICAL: container uptime', '00:00:48')

        self.assertEqual(len(self.post.call_args_list), 1)

    def test_duplicate_reopening_posts_once(self):
        alert_id = self._send('critical', 'CRITICAL: container uptime', '00:00:47')
        self._action(alert_id, 'close', 'closed by hand')
        self._send('critical', 'CRITICAL: container uptime', '00:00:12')

        self.assertEqual(self._messages(), [
            (RED, self._desc('CRITICAL: container uptime', 'Open', '00:00:47')),
            (BLUE, self._desc('closed by hand', 'Closed', '00:00:47')),
            (RED, self._desc('CRITICAL: container uptime', 'Open', '00:00:12')),
        ])

    def test_user_action_posts_once(self):
        alert_id = self._send('critical', 'CRITICAL: container uptime', '00:00:47')
        self._action(alert_id, 'ack', 'looking into it')

        self.assertEqual(self._messages()[1:], [
            (BLUE, self._desc('looking into it', 'Ack', '00:00:47')),
        ])

    def test_environment_shown_on_request(self):
        with mock.patch('alerta_discord.DISCORD_SHOW_ENVIRONMENT', True):
            self._send('critical', 'CRITICAL: container uptime', '00:00:47')

        self.assertEqual(self._messages(), [
            (RED, self._desc('CRITICAL: container uptime', 'Open', '00:00:47',
                             '\n**Environment** Production')),
        ])

    def test_markdown_in_values_is_escaped(self):
        self.resource = 'mgmt_' + uuid.uuid4().hex[:8] + '_node'
        self._send('critical', 'CRITICAL: *container* uptime', '00:00:47')

        description = self._messages()[0][1]
        self.assertIn('CRITICAL: \\*container\\* uptime', description)
        self.assertIn('**Resource** ' + self.resource.replace('_', '\\_'),
                      description)
