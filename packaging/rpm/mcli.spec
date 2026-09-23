Name: javli
Version: VERSION
Release: 1%{?dist}
Summary: Minecraft Command-Line Launcher
License: MIT
BuildArch: ARCH

%description
Launch modern and historical Minecraft from the terminal.

%install
mkdir -p %{buildroot}/usr/bin
install -m 0755 %{_sourcedir}/javli %{buildroot}/usr/bin/javli

%files
/usr/bin/javli
