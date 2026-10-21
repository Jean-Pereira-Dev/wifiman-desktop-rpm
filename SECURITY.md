# Security policy

This repository maintains unofficial RPM packaging and build automation for
Ubiquiti WiFiman Desktop. It redistributes the upstream application binary;
it does not maintain that application's source code.

## Reporting a vulnerability

For vulnerabilities in these packaging scripts, RPM scriptlets, or workflows,
use [GitHub private vulnerability reporting](https://github.com/Jean-Pereira-Dev/wifiman-desktop-rpm/security/advisories/new).
Include the affected version, distribution, reproduction steps, and impact.
Do not include credentials, private network details, or unnecessary personal data.

Report vulnerabilities in WiFiman itself through
[Ubiquiti's security reporting process](https://www.ui.com/security).

## Supported packages

Use the latest published package for a target currently tested by the workflow:
supported stable Fedora releases, Enterprise Linux 10, openSUSE Leap 16.0,
and openSUSE Tumbleweed, on x86_64. Older RPMs retained in release assets are
not separately maintained. AlmaLinux and Rocky Linux 10 are installation-test
targets for the Enterprise Linux package.

Build and installation checks do not constitute a security audit of the
upstream binary or a test of every graphical and VPN feature. GitHub dependency
alerts do not cover every library embedded in the upstream application.

## SELinux compatibility settings

On Fedora and Enterprise Linux, installation makes the `init_t` and `iptables_t`
domains permissive when SELinux is enabled. This affects all processes in those
domains, including processes unrelated to WiFiman, and persists after uninstall.
See the README for the commands and reversal procedure. These settings are a
compatibility workaround, not a narrowly scoped WiFiman SELinux policy.
They are not applied by the openSUSE RPM.
