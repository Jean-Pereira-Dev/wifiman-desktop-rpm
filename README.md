[![Copr Build Status](https://copr.fedorainfracloud.org/coprs/jeanpereira/wifiman/package/wifiman-desktop/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/jeanpereira/wifiman/)

# RPM Package: wifiman-desktop

This repository holds the RPM package source for [wifiman-desktop](https://www.ui.com/download/app/wifiman-desktop).

> WiFiman is here to save your home or office network from sluggish surfing, endless buffering, and congested data 
> channels.

> [!NOTE]  
> This is a wrapper package of the WiFiman Desktop releases for Ubuntu available [here](https://www.ui.com/download/app/wifiman-desktop)
> and is in no way affliated with or maintained by [Ubiquity Inc](https://ui.com/) for any application support or questions please see
> [here](https://help.ui.com/hc/en-us).


## Installation

### From Copr Repository (Recommended)

You can install this package by enabling the Copr repository at [jeanpereira/wifiman](https://copr.fedorainfracloud.org/coprs/jeanpereira/wifiman/):

```sh
dnf copr enable jeanpereira/wifiman
dnf install wifiman-desktop
```

### From GitHub Releases

Download the Fedora 43 RPM from the [releases page](https://github.com/Jean-Pereira-Dev/wifiman-desktop-rpm/releases):

```sh
dnf install ./wifiman-desktop-1.3.0-*.fc43.x86_64.rpm
```

> **Note:** GitHub releases contain only Fedora 43 RPMs. For other Fedora versions, use the Copr repository above.

## Usage

Once installed you can enable and start the daemon using the following command, then launch the application.

```sh
systemctl enable --now wifiman-desktop.service
```

## Automated updates and recovery

The daily workflow reads Ubiquiti's Linux manifest, validates the version and
package URL, and checks the downloaded package against the manifest SHA-256.
It builds on the self-hosted Linux x64 runner using Fedora 43, tests installation and
removal, and uploads RPM/SRPM artifacts. PRs run the same checks without
publishing releases or submitting to Copr. External PRs use GitHub-hosted
runners so untrusted changes do not execute on the private runner.

Scheduled runs skip only when the upstream version has a published release
containing both a nonempty Fedora 43 x86_64 RPM and an SRPM. Missing assets,
draft releases, and failed uploads can therefore be retried. Pushes and manual
runs always build. New releases remain drafts until their assets are uploaded.
Copr submission is optional (`COPR_LOGIN` and `COPR_TOKEN` repository secrets);
when configured, the workflow waits for Copr before publishing the release.

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
