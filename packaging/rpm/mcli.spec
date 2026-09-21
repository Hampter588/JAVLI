Name: mcli
Version: VERSION
Release: 1%{?dist}
Summary: Minecraft Command-Line Launcher
License: MIT
BuildArch: ARCH
%description
Launch modern and historical Minecraft from the terminal.
%install
mkdir -p %{buildroot}/usr/bin
install -m 0755 %{_sourcedir}/mcli %{buildroot}/usr/bin/mcli
%files
/usr/bin/mcli
