#!/usr/bin/env python3
"""Use Fedora's supported stable releases as the single CI/Copr target list."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess

BODHI_URL = 'https://bodhi.fedoraproject.org/releases/?state=current'
CHROOTS_URL = 'https://copr.fedorainfracloud.org/api_3/mock-chroots/list'


def fetch_json(url):
    return json.loads(subprocess.check_output([
        'curl', '--fail', '--silent', '--show-error', '--location', '--retry', '3',
        '--connect-timeout', '15', '--max-time', '60', url], text=True))


def fetch_releases():
    result = fetch_json(BODHI_URL)
    pages = int(result.get('pages', 1))
    if not 1 <= pages <= 100:
        raise ValueError('Invalid Bodhi pagination')
    for page in range(2, pages + 1):
        result['releases'].extend(fetch_json(BODHI_URL + '&page=' + str(page))['releases'])
    return result


def discover(releases, available, today=None):
    if releases.get('total', len(releases['releases'])) != len(releases['releases']):
        raise ValueError('Incomplete Fedora release metadata')
    today = today or date.today()
    versions = set()
    for release in releases['releases']:
        if release.get('id_prefix') != 'FEDORA' or release.get('state') != 'current':
            continue
        version = release.get('version', '')
        if not re.fullmatch(r'[1-9][0-9]*', version) or release.get('name') != 'F' + version:
            raise ValueError('Invalid Fedora release metadata')
        if release.get('eol') and date.fromisoformat(release['eol']) <= today:
            continue
        if release.get('released_on') and date.fromisoformat(release['released_on']) > today:
            continue
        versions.add(int(version))
    if not versions:
        raise ValueError('No supported stable Fedora releases found; refusing an empty matrix')
    versions = [str(version) for version in sorted(versions)]
    chroots = [f'fedora-{version}-x86_64' for version in versions] + ['epel-10-x86_64', 'opensuse-leap-16.0-x86_64', 'opensuse-tumbleweed-x86_64']
    missing = set(chroots) - set(available)
    if missing:
        raise ValueError('Configured targets not available in Copr yet: ' + ', '.join(sorted(missing)))
    return {'fedora_versions': versions, 'copr_chroots': chroots, 'latest_fedora': versions[-1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--releases', type=Path)
    parser.add_argument('--chroots', type=Path)
    args = parser.parse_args()
    try:
        releases = json.loads(args.releases.read_text()) if args.releases else fetch_releases()
        available = json.loads(args.chroots.read_text()) if args.chroots else fetch_json(CHROOTS_URL)
        result = discover(releases, available)
        output = ''.join(f'{key}={json.dumps(value, separators=(",", ":")) if isinstance(value, list) else value}\n' for key, value in result.items())
        print(output, end='')
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
                stream.write(output)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Fedora target discovery failed: {error}\n')


if __name__ == '__main__':
    main()
