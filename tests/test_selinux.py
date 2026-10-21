"""Exercise the actual spec scriptlet with stub commands, never host policy."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = (Path(__file__).resolve().parents[1] / 'wifiman-desktop.spec').read_text()
BLOCK = SPEC.split('# BEGIN WIFIMAN SELINUX WORKAROUND\n')[1].split('# END WIFIMAN SELINUX WORKAROUND')[0]

class SelinuxScriptletTests(unittest.TestCase):
    def run_block(self, enabled, failure=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commands = {
                'selinuxenabled': f'#!/bin/sh\nexit {0 if enabled else 1}\n',
                'semanage': '#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALLS"\nexit "$FAILURE"\n',
            }
            for name, content in commands.items():
                script = root / name
                script.write_text(content)
                script.chmod(0o755)
            calls = root / 'calls'
            result = subprocess.run(['/bin/sh', '-c', BLOCK], env={**os.environ, 'PATH': directory, 'CALLS': str(calls), 'FAILURE': str(failure)}, capture_output=True)
            return result.returncode, calls.read_text().splitlines() if calls.exists() else []

    def test_enabled_applies_both_domains(self):
        self.assertEqual(self.run_block(True), (0, ['permissive -a init_t', 'permissive -a iptables_t']))

    def test_disabled_skips_policy_changes(self):
        self.assertEqual(self.run_block(False), (0, []))

    def test_failure_is_reported_before_service_can_start(self):
        self.assertEqual(self.run_block(True, failure=2), (2, ['permissive -a init_t']))
