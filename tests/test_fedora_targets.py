from datetime import date
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
fedora = load('fedora_targets')
copr = load('sync_copr')

def release(version, state='current', **kwargs):
    return dict(name='F' + version, version=version, state=state, id_prefix='FEDORA', **kwargs)

class FedoraTargetsTests(unittest.TestCase):
    def test_only_supported_stable_releases(self):
        records = [release('43'), release('44'), release('45', 'pending'),
                   release('46', 'pending'), release('42', eol='2026-06-01'),
                   dict(name='EPEL-10', version='10', id_prefix='FEDORA-EPEL', state='current')]
        result = fedora.discover({'releases': records}, ['fedora-43-x86_64', 'fedora-44-x86_64', 'epel-10-x86_64', 'opensuse-leap-16.0-x86_64', 'opensuse-tumbleweed-x86_64'], date(2026, 10, 21))
        self.assertEqual(result['fedora_versions'], ['43', '44'])
        self.assertEqual(result['latest_fedora'], '44')

    def test_new_stable_release_is_added_without_code_change(self):
        result = fedora.discover({'releases': [release('44'), release('45')]}, ['fedora-44-x86_64', 'fedora-45-x86_64', 'epel-10-x86_64', 'opensuse-leap-16.0-x86_64', 'opensuse-tumbleweed-x86_64'])
        self.assertEqual(result['fedora_versions'], ['44', '45'])

    def test_empty_or_unavailable_target_fails_closed(self):
        for records, available in [([], []), ([release('45')], []), ([release('rawhide')], [])]:
            with self.subTest(records=records), self.assertRaises(ValueError):
                fedora.discover({'releases': records}, available)

    def test_future_release_date_is_not_stable_yet(self):
        with self.assertRaises(ValueError):
            fedora.discover({'releases': [release('45', released_on='2026-11-01')]}, ['fedora-45-x86_64'], date(2026, 10, 21))

    def test_copr_adds_targets_and_preserves_existing(self):
        client = Mock()
        client.mock_chroot_proxy.get_list.return_value = {'fedora-44-x86_64': ''}
        client.project_proxy.get.return_value = SimpleNamespace(chroot_repos={'fedora-43-x86_64': '', 'epel-10-x86_64': ''}, follow_fedora_branching=False)
        copr.sync(client, ['fedora-44-x86_64'])
        client.project_proxy.edit.assert_called_once_with(ownername='jeanpereira', projectname='wifiman',
            chroots=['epel-10-x86_64', 'fedora-43-x86_64', 'fedora-44-x86_64'], follow_fedora_branching=True)

    def test_copr_sync_is_idempotent(self):
        client = Mock()
        client.mock_chroot_proxy.get_list.return_value = {'fedora-44-x86_64': ''}
        client.project_proxy.get.return_value = SimpleNamespace(chroot_repos={'fedora-44-x86_64': ''}, follow_fedora_branching=True)
        copr.sync(client, ['fedora-44-x86_64'])
        client.project_proxy.edit.assert_not_called()
        client.project_chroot_proxy.edit.assert_not_called()

    def test_epel_is_required_and_can_be_added(self):
        with self.assertRaises(ValueError):
            fedora.discover({'releases': [release('44')]}, ['fedora-44-x86_64'])
        client = Mock()
        client.mock_chroot_proxy.get_list.return_value = {'epel-10-x86_64': ''}
        client.project_proxy.get.return_value = SimpleNamespace(chroot_repos={'fedora-44-x86_64': ''}, follow_fedora_branching=True)
        copr.sync(client, ['epel-10-x86_64'])
        client.project_proxy.edit.assert_called_once_with(ownername='jeanpereira', projectname='wifiman',
            chroots=['epel-10-x86_64', 'fedora-44-x86_64'], follow_fedora_branching=True)

    def test_unvalidated_enterprise_targets_are_rejected(self):
        for target in ['epel-8-x86_64', 'epel-9-x86_64', 'epel-11-x86_64']:
            with self.subTest(target=target), self.assertRaises(ValueError):
                copr.sync(Mock(), [target])

    def test_tumbleweed_bootstrap_avoids_image_repository_skew(self):
        target = 'opensuse-tumbleweed-x86_64'
        for current in [None, 'default', 'image', 'on']:
            client = Mock()
            client.mock_chroot_proxy.get_list.return_value = {target: ''}
            client.project_proxy.get.return_value = SimpleNamespace(
                chroot_repos={target: ''}, follow_fedora_branching=True)
            client.project_chroot_proxy.get.return_value = SimpleNamespace() if current is None else SimpleNamespace(bootstrap=current)
            copr.sync(client, [target])
            if current == 'on':
                client.project_chroot_proxy.edit.assert_not_called()
            else:
                client.project_chroot_proxy.edit.assert_called_once_with(
                    ownername='jeanpereira', projectname='wifiman',
                    chrootname=target, bootstrap='on')
            client.project_proxy.edit.assert_not_called()
