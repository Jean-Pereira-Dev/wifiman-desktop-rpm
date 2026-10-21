import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_version', ROOT / 'scripts/check_version.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.manifest = dict(version='1.3.0', platforms={'linux-x86_64': 'https://desktop.wifiman.com/wifiman-desktop-1.3.0-amd64.deb'}, checksums={'linux-x86_64': 'a' * 64})

    def test_update_and_current(self):
        self.assertEqual(module.discover(self.manifest, 'Version: 1.2.8')['version_changed'], 'true')
        self.assertEqual(module.discover(self.manifest, 'Version: 1.3.0')['version_changed'], 'false')

    def test_numeric_comparison(self):
        self.assertEqual(module.discover(self.manifest, 'Version: 1.2.10')['latest_version'], '1.3.0')
        with self.assertRaises(ValueError):
            module.discover(self.manifest, 'Version: 1.10.0')

    def test_invalid_manifest_fields(self):
        for field, value in [('version', 'unknown'), ('version', '1.3.0\nforged=true'), ('version', None), ('platforms', {}), ('checksums', {})]:
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.manifest)
                data[field] = value
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    module.discover(data, 'Version: 1.2.8')

    def test_url_and_checksum(self):
        for url in ['https://evil.example/wifiman-desktop-1.3.0-amd64.deb', 'http://desktop.wifiman.com/wifiman-desktop-1.3.0-amd64.deb', 'https://desktop.wifiman.com/wifiman-desktop-1.2.8-amd64.deb']:
            self.manifest['platforms']['linux-x86_64'] = url
            with self.assertRaises(ValueError):
                module.discover(self.manifest, 'Version: 1.2.8')
        self.setUp()
        self.manifest['checksums']['linux-x86_64'] = 'bad'
        with self.assertRaises(ValueError):
            module.discover(self.manifest, 'Version: 1.2.8')

    def test_old_url_format(self):
        self.manifest['platforms']['linux-x86_64'] = 'https://desktop.wifiman.com/wifiman-desktop-1.3.0-linux-amd64.deb'
        self.assertEqual(module.discover(self.manifest, 'Version: 1.2.8')['latest_version'], '1.3.0')

    def test_invalid_json_fails_without_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / 'manifest.json'
            manifest.write_text('<html>Unavailable</html>')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/check_version.py'), '--manifest', str(manifest)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, '')
            self.assertIn('Version discovery failed', result.stderr)
