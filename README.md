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
dnf install wifiman-desktop-1.2.8-1.fc43.x86_64.rpm
```

> **Note:** GitHub releases contain only Fedora 43 RPMs. For other Fedora versions, use the Copr repository above.

## Usage

Once installed you can enable and start the daemon using the following command, then launch the application.

```sh
systemctl enable --now wifiman-desktop.service
```
