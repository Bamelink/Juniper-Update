# callback plugin that writes a condensed Markdown report
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase
import json
import os

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'juniper_report'
    CALLBACK_TYPE = 'notification'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.reports = {}

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        if host not in self.reports:
            self.reports[host] = []
        self.reports[host].append({
            'task': result.task_name,
            'status': 'ok',
            'result': result._result,
        })

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        if host not in self.reports:
            self.reports[host] = []
        self.reports[host].append({
            'task': result.task_name,
            'status': 'failed',
            'result': result._result,
        })

    def v2_playbook_on_stats(self, stats):
        out = ['# Juniper upgrade report\n']
        for host, entries in self.reports.items():
            out.append(f'## {host}\n')
            for e in entries:
                out.append(f"- **{e['task']}**: {e['status']}\n")
        path = os.path.join(os.getcwd(), 'ansible-report.md')
        with open(path, 'w') as f:
            f.write('\n'.join(out))
        self._display.display(f"Report written to {path}")
