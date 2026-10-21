#!/usr/bin/env python3
"""Add CI's stable Fedora targets without removing any existing Copr targets."""
import argparse
import json
import re


def sync(client, desired):
    if not desired or any(not re.fullmatch(r'(?:fedora-[1-9][0-9]*|epel-10)-x86_64', target) for target in desired):
        raise ValueError('Invalid Copr targets')
    available = client.mock_chroot_proxy.get_list()
    missing = set(desired) - set(available)
    if missing:
        raise ValueError('Unavailable Copr targets: ' + ', '.join(sorted(missing)))
    project = client.project_proxy.get(ownername='jeanpereira', projectname='wifiman')
    existing = set(project.chroot_repos)
    if not set(desired).issubset(existing) or not project.follow_fedora_branching:
        client.project_proxy.edit(ownername='jeanpereira', projectname='wifiman',
                                  chroots=sorted(existing | set(desired)), follow_fedora_branching=True)
    print('Copr targets ready: ' + ', '.join(desired))


if __name__ == '__main__':
    from copr.v3 import Client
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--chroots', required=True, help='JSON array from Fedora discovery')
    args = parser.parse_args()
    sync(Client.create_from_config_file(args.config), json.loads(args.chroots))
