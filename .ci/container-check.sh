#!/usr/bin/env bash
set -euo pipefail
mkdir /build
cp /repo/PKGBUILD /build/
chown builder:builder /build
cd /build
runuser -u builder -- makepkg --syncdeps --noconfirm
runuser -u builder -- makepkg --printsrcinfo > /out/.SRCINFO
mapfile -t packages < <(runuser -u builder -- makepkg --packagelist)
test "${#packages[@]}" -eq 1
package=${packages[0]}
namcap PKGBUILD "$package" | tee /out/namcap.log
if grep -q ' E: ' /out/namcap.log; then exit 1; fi
pacman -U --noconfirm "$package"
desktop-file-validate /usr/share/applications/localflow.desktop
test -f /usr/share/icons/hicolor/256x256/apps/localflow.png
test -s /usr/share/licenses/localflow-bin/README.md
test -s /usr/share/licenses/localflow-bin/THIRD_PARTY_LICENSES.md
# Run as an ordinary user with no display, models or microphone.
runuser -u builder -- timeout 15 localflow --help > /out/cli-help.txt
runuser -u builder -- timeout 15 localflow --version > /out/cli-version.txt
version=$(awk -F= '/^pkgver=/{print $2}' PKGBUILD)
grep -Fx "localflow $version" /out/cli-version.txt
ldd /usr/bin/localflow | tee /out/ldd.txt
if grep -q 'not found' /out/ldd.txt; then exit 1; fi
pacman -U --noconfirm "$package"
cp "$package" /out/
pacman -R --noconfirm localflow-bin
test ! -e /usr/bin/localflow
test ! -e /usr/share/applications/localflow.desktop
test ! -e /usr/share/icons/hicolor/256x256/apps/localflow.png
test ! -e /usr/share/licenses/localflow-bin
echo 'Package build, install, CLI, dependency, reinstall and removal checks passed.'
