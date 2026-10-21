[![Copr Build Status](https://copr.fedorainfracloud.org/coprs/jeanpereira/wifiman/package/wifiman-desktop/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/jeanpereira/wifiman/)

# RPM Package: wifiman-desktop

This repository holds the RPM package source for [wifiman-desktop](https://www.ui.com/download/app/wifiman-desktop).

> WiFiman is here to save your home or office network from sluggish surfing, endless buffering, and congested data 
> channels.

> [!NOTE]  
> This is a wrapper package of the WiFiman Desktop releases for Ubuntu available [here](https://www.ui.com/download/app/wifiman-desktop)
> and is in no way affiliated with or maintained by [Ubiquiti Inc](https://ui.com/) for any application support or questions please see
> [here](https://help.ui.com/hc/en-us).


## Installation

### From Copr Repository (Recommended)

You can install this package by enabling the Copr repository at [jeanpereira/wifiman](https://copr.fedorainfracloud.org/coprs/jeanpereira/wifiman/):

```sh
dnf copr enable jeanpereira/wifiman
dnf install wifiman-desktop
```

### From GitHub Releases

Download the RPM matching your Fedora release from the [releases page](https://github.com/Jean-Pereira-Dev/wifiman-desktop-rpm/releases):

```sh
dnf install ./wifiman-desktop-1.3.0-*.fc$(rpm -E %fedora).x86_64.rpm
```

> GitHub releases contain separate RPMs for each supported stable Fedora release.

## Usage

Once installed you can enable and start the daemon using the following command, then launch the application.

```sh
systemctl enable --now wifiman-desktop.service
```

## Automated updates and recovery

The daily workflow reads Ubiquiti's Linux manifest, validates the version and
package URL, and checks the downloaded package against the manifest SHA-256.
It discovers supported stable Fedora releases from the official Bodhi API,
then builds and tests each release on the self-hosted Linux x64 runner, including installation and
removal, and uploads RPM/SRPM artifacts. PRs run the same checks without
publishing releases or submitting to Copr. External PRs use GitHub-hosted
runners so untrusted changes do not execute on the private runner.

Scheduled runs skip only when the upstream version has a published release
containing a nonempty x86_64 RPM and SRPM for every current Fedora target,
plus a successful Copr marker for that exact target list when Copr is configured. Missing assets, draft
releases, failed uploads, and failed Copr builds can therefore be retried. Pushes and manual
runs always build. New releases remain drafts until their assets are uploaded.
Copr submission is optional (`COPR_LOGIN` and `COPR_TOKEN` repository secrets);
when configured, the workflow waits for the Copr build result and records
success in the GitHub release metadata. GitHub RPMs are published immediately
after the Fedora and Enterprise Linux installation tests pass, independently of Copr credentials.
If Copr fails, the run reports failure and the next daily check retries it,
even when the GitHub RPM assets already exist. After renewing expired Copr
credentials in repository secrets, run the workflow manually to retry immediately.

The daily schedule runs at **02:17 UTC** (03:17 in Berlin in winter,
04:17 in summer). The version-check job makes an empty maintenance commit
with `[skip ci]` after 45 days without commits to keep the schedule active.
It requires the workflow's `contents: write` permission and permission to
push to the default branch; branch protection must allow that maintenance push.

**GitHub can disable schedules after 60 days without repository activity.**
In Actions, select **Build and Test RPM**, choose **Enable workflow** if shown,
and then **Run workflow** on the default branch. A cron change alone does not
prevent future inactivity disabling. The maintenance step prevents this during
normal scheduled operation; if branch protection blocks it, arrange an external
authenticated trigger or allow the push.
The checked-in spec is a baseline; each build sets its version and source from
the validated manifest without committing generated version changes.

Local discovery and regression checks:

```sh
bash scripts/check-version.sh
python3 -m unittest discover -s tests -v
node --test tests/release.test.cjs
```

Discovery returns 0 on success (including when a new version is available),
and nonzero on network, JSON, validation, or downgrade errors. Use
`--manifest /path/to/manifest.json` for an offline check. This replaces the old
exit-10 update convention.

## Fedora SELinux compatibility

On installation and upgrade, the RPM installs `policycoreutils-python-utils`
and `libselinux-utils` and applies these settings before starting the service
when SELinux is enabled:

```sh
semanage permissive -a init_t
semanage permissive -a iptables_t
```

These settings persist and apply system-wide to both domains, including
processes unrelated to WiFiman. Other SELinux domains remain enforcing.
Failures are reported by the RPM post-install scriptlet. Hosts and build
containers with SELinux disabled skip the commands. The settings are retained
on uninstall to preserve any pre-existing administrator configuration.
To reverse them manually when no longer needed:

```sh
sudo semanage permissive -d init_t
sudo semanage permissive -d iptables_t
```

## Automatic Fedora coverage

Every daily check queries Fedora Bodhi for releases with `state=current`,
filters out EPEL, future releases and EOL releases, and verifies the matching
x86_64 chroots exist in Copr. There is no hard-coded Fedora version list.
Beta and Rawhide releases are excluded. A newly stable Fedora release triggers
builds even if the WiFiman version is unchanged.

Each matrix job builds, installs, validates and removes its RPM in the matching
Fedora container. All targets must pass before the release is published. Copr
is then synchronized by adding missing targets while preserving existing
project targets and enabling `follow_fedora_branching`. Each target's native SRPM is submitted
to its matching Copr chroot; older/custom/beta targets in
the project are preserved but not submitted by this workflow. EOL Fedora
versions stop being tested automatically. If discovery fails or a newly stable
chroot is unavailable, the workflow fails visibly and retries the next day.

The JavaScript actions use Node 24 runtimes; `setup-node` also selects Node 24
for the regression tests. The self-hosted runner must support Node 24
(Actions runner 2.327.1 or newer).


### Enterprise Linux 10

The daily pipeline also builds an x86_64 EL10 RPM on AlmaLinux 10, tests
installation/removal of the same package on Rocky Linux 10, and adds
`epel-10-x86_64` to Copr before submitting the SRPM. EPEL and CRB repositories
are required for dependencies. GitHub releases include the `.el10` RPM/SRPM.
Publishing waits for both Fedora and EL10 tests; Copr success receipts include
EPEL 10 so an existing Fedora-only release cannot suppress the first EL10 build.
On AlmaLinux 10 and Rocky Linux 10, enable the dependency repositories before
installing from Copr:

```sh
sudo dnf install dnf-plugins-core epel-release
sudo dnf config-manager --set-enabled crb
sudo dnf copr enable jeanpereira/wifiman
sudo dnf install wifiman-desktop
```

RHEL 10 uses CodeReady Builder instead of the `crb` repository name; follow the
[official EPEL setup instructions](https://docs.fedoraproject.org/en-US/epel/getting-started/)
for that system first. The spec declares packages and shared-library requirements;
it does not enable third-party repositories on the user's system.

Container tests verify packaging, not a graphical session or live Teleport VPN.

AlmaLinux and Rocky Linux currently support major versions 8, 9 and 10, with
only the latest minor release of each supported. WiFiman 1.3.0's prebuilt
binaries require GLIBC_2.34 (EL8 has 2.28); EL9 lacks the WebKitGTK 4.1 and
libsoup 3 dependencies in the repositories checked. These targets are not enabled.
### openSUSE

Leap 16.0 and Tumbleweed have separate build/install/remove jobs. Their RPMs
use `.suse1600` and `.suse1699` respectively; install the package matching your
system. The spec uses openSUSE dependencies and service macros, and does not
apply the Fedora/EL SELinux permissive-domain workaround on openSUSE.
Copr targets `opensuse-leap-16.0-x86_64` and `opensuse-tumbleweed-x86_64` are
added automatically before submission. All configured targets must pass before
GitHub release publication. openSUSE versions are explicitly validated targets;
new Leap releases require testing and updating the target list.

Leap 15.6 reached end of life in April 2026; Leap 16.1 remains a release
candidate as of 2026-10-21. Slowroll and immutable variants are not tested.
For Leap 16.0, enable the Copr repository with:

```sh
sudo zypper addrepo https://copr.fedorainfracloud.org/coprs/jeanpereira/wifiman/repo/opensuse-leap-16.0/jeanpereira-wifiman-opensuse-leap-16.0.repo
sudo zypper refresh
sudo zypper install wifiman-desktop
```

For Tumbleweed, replace both occurrences of `opensuse-leap-16.0` in that URL
with `opensuse-tumbleweed`. Review the repository signing key when prompted.

Supported-release references: [AlmaLinux](https://wiki.almalinux.org/release-notes/),
[Rocky Linux](https://docs.rockylinux.org/releases/), and
[openSUSE](https://get.opensuse.org/).
