#!/usr/bin/env python3
"""Discover the official Linux package; never turn network errors into versions."""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

MANIFEST_URL = "https://desktop.wifiman.com/wifiman-desktop-linux-manifest.json"
VERSION = r"[0-9]+\.[0-9]+\.[0-9]+"


def discover(manifest, spec):
    match = re.search(r"^Version:\s*(\S+)\s*$", spec, re.M)
    if not match or not re.fullmatch(VERSION, match[1]):
        raise ValueError("Spec must contain a numeric major.minor.patch Version")
    current = match[1]
    latest = manifest["version"]
    if not isinstance(latest, str) or not re.fullmatch(VERSION, latest):
        raise ValueError("Invalid upstream version")
    url = manifest["platforms"]["linux-x86_64"]
    checksum = manifest["checksums"]["linux-x86_64"]
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "desktop.wifiman.com"
            or parsed.query or parsed.fragment
            or parsed.path not in (f"/wifiman-desktop-{latest}-amd64.deb",
                                   f"/wifiman-desktop-{latest}-linux-amd64.deb")):
        raise ValueError("Unexpected upstream Linux package URL")
    if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", checksum):
        raise ValueError("Invalid upstream SHA-256")
    if tuple(map(int, latest.split("."))) < tuple(map(int, current.split("."))):
        raise ValueError("Upstream version is older than the spec; refusing downgrade")
    return dict(current_version=current, latest_version=latest,
                version_changed=str(current != latest).lower(),
                download_url=url, sha256=checksum.lower())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="Read a saved manifest (offline testing)")
    parser.add_argument("--spec", type=Path, default=Path(os.environ.get("SPEC_FILE", "wifiman-desktop.spec")))
    args = parser.parse_args()
    try:
        data = args.manifest.read_text() if args.manifest else subprocess.check_output(
            ["curl", "--fail", "--silent", "--show-error", "--location",
             "--retry", "3", "--connect-timeout", "15", "--max-time", "60", MANIFEST_URL], text=True)
        result = discover(json.loads(data), args.spec.read_text())
        output = "".join(f"{key}={value}\n" for key, value in result.items())
        print(output, end="")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
                stream.write(output)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Version discovery failed: {error}\n")


if __name__ == "__main__":
    main()
