#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up build environment ==="
# Enterprise Linux needs EPEL and CRB for desktop/build dependencies.
if [ "$(rpm -E '%{?rhel}')" = 10 ]; then
  dnf install -y dnf-plugins-core epel-release
  dnf config-manager --set-enabled crb
fi
dnf install -y rpm-build rpmdevtools dnf-plugins-core
dnf builddep -y wifiman-desktop.spec

echo "=== Setting up build directory ==="
rpmdev-setuptree

echo "=== Copying verified source files ==="
cp /build/sources/*.deb ~/rpmbuild/SOURCES/

echo "=== Building SRPM ==="
rpmbuild -bs wifiman-desktop.spec

echo "=== Building RPM ==="
rpmbuild -bb wifiman-desktop.spec

echo "=== Build complete - listing artifacts ==="
echo "SRPMS:"
ls -lh ~/rpmbuild/SRPMS/
echo "RPMS:"
ls -lh ~/rpmbuild/RPMS/*/

echo "=== Testing installation ==="
RPM_FILE=$(find ~/rpmbuild/RPMS -name "wifiman-desktop-*.rpm" -type f ! -name "*.src.rpm" | head -1)
if [ -z "$RPM_FILE" ]; then
  echo "ERROR: No RPM file found"
  exit 1
fi

echo "Installing: $RPM_FILE"
dnf install -y "$RPM_FILE"

echo "Verifying package installation..."
rpm -qi wifiman-desktop

if [ ! -f /usr/bin/wifiman-desktop ]; then
  echo "ERROR: Binary not found in /usr/bin"
  exit 1
fi

if [ ! -f /usr/lib/systemd/system/wifiman-desktop.service ]; then
  echo "ERROR: Service file not found"
  exit 1
fi

if [ ! -f /usr/share/applications/wifiman-desktop.desktop ]; then
  echo "ERROR: Desktop file not found"
  exit 1
fi

# Verify the daemon and hidden configuration survive repackaging.
test -x /usr/lib/wifiman-desktop/wifiman-desktopd
test -f /usr/lib/wifiman-desktop/.env

desktop-file-validate /usr/share/applications/wifiman-desktop.desktop

echo "✓ Installation test PASSED"

echo "=== Testing uninstallation ==="
dnf remove -y wifiman-desktop

if rpm -q wifiman-desktop &>/dev/null; then
  echo "ERROR: Package still installed after removal"
  exit 1
fi

echo "✓ Uninstallation test PASSED"

mkdir -p /build/rpmbuild/{SRPMS,RPMS}
cp ~/rpmbuild/SRPMS/*.src.rpm /build/rpmbuild/SRPMS/
cp -r ~/rpmbuild/RPMS/* /build/rpmbuild/RPMS/
