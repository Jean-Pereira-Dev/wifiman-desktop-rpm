%global _hardened_build 1
%define _build_id_links none
%define debug_package %{nil}

Name:     wifiman-desktop
Version:  1.2.8
Release:  1%{?dist}
Summary:  Discover devices and access Teleport VPNs
License:  MIT
Vendor:   Ubiquiti Inc. <monitoring@wifiman.com>
URL:      https://wifiman.com/

%ifarch x86_64
Source0:  https://desktop.wifiman.com/wifiman-desktop-%{version}-amd64.deb
%endif

BuildRequires: binutils
BuildRequires: desktop-file-utils
BuildRequires: gzip
BuildRequires: systemd-units
BuildRequires: tar
BuildRequires: xz

Requires: gtk3
Requires: libsecret
Requires: libuuid
Requires: at-spi2-core
Requires: xdg-utils
Requires: libXtst
Requires: libXScrnSaver
Requires: nss
Requires: libnotify
Requires: wireguard-tools
Requires: systemd

Recommends: libappindicator-gtk3

%description
WiFiman is here to save your home or office network from sluggish surfing, endless buffering, and congested data channels.
With this free-to-use (and ad-free) app you can:

- Detect and connect to all available Wi-Fi networks devices instantly.
- Scan network subnet for details on available devices, using Bonjour, SNMP, NetBIOS, and Ubiquiti discovery protocols.
- Conduct download/upload speed tests, store results, compare network performance, and share your insights with others.
- Relocate your access points (APs) to nearby data channels to instantly increase signal strength and reduce traffic volume.
- Connect remotely to your UniFi network via Teleport VPN.

%prep
%setup -cT
ar x %{SOURCE0}
tar xf data.tar.gz

%build

%install
# Install binary
install -D -m 755 usr/bin/wifiman-desktop %{buildroot}%{_bindir}/wifiman-desktop

# Install lib directory (keep /usr/lib path to match service ExecStart)
mkdir -p %{buildroot}%{_prefix}/lib/wifiman-desktop
cp -a usr/lib/wifiman-desktop/* %{buildroot}%{_prefix}/lib/wifiman-desktop/

# Install systemd service
install -D -m 644 usr/lib/wifiman-desktop/wifiman-desktop.service %{buildroot}%{_unitdir}/%{name}.service

# Install desktop file and icons
mkdir -p %{buildroot}%{_datadir}
cp -a usr/share/* %{buildroot}%{_datadir}/

%check
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{name}.desktop

%post
%systemd_post %{name}.service
/usr/bin/systemctl enable --now %{name}.service >/dev/null 2>&1 || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
update-mime-database %{_datadir}/mime &>/dev/null || :
update-desktop-database %{_datadir}/applications &>/dev/null || :

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files
%defattr(-,root,root,-)
%{_bindir}/wifiman-desktop
%{_prefix}/lib/wifiman-desktop/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_unitdir}/%{name}.service

%changelog
* Thu Feb 12 2026 GitHub Actions <actions@github.com> 1.2.8-1
- Update to version 1.2.8 with new FHS-compliant structure
- Remove obsolete patches (package now uses standard paths)
- Binary now in /usr/bin, libraries in /usr/lib/wifiman-desktop

* Thu Sep 05 2024 Arun Babu Neelicattu <arun.neelicattu@gmail.com> 0.3.0-3
- spec: include all arch debs in srpm (arun.neelicattu@gmail.com)

* Thu Sep 05 2024 Arun Babu Neelicattu <arun.neelicattu@gmail.com> 0.3.0-2
- tito: fetch sources for build (arun.neelicattu@gmail.com)

* Thu Sep 05 2024 Arun Babu Neelicattu <arun.neelicattu@gmail.com> 0.3.0-1
- Release 0.30.0 package built with tito

