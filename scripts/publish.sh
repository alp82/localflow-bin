#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root=$PWD
# A queued old workflow must never overwrite a newer main-branch package.
if [[ -n ${GITHUB_SHA:-} ]]; then
  latest=$(git ls-remote origin refs/heads/main | cut -f1)
  if [[ "$latest" != "$GITHUB_SHA" ]]; then
    echo 'A newer main commit exists; skipping this outdated workflow.'
    exit 0
  fi
fi
checkout=$(mktemp -d)
trap 'rm -rf "$checkout"' EXIT
git -c init.defaultBranch=master clone ssh://aur@aur.archlinux.org/localflow-bin.git "$checkout/aur"
cp PKGBUILD .SRCINFO LICENSE "$checkout/aur/"
cd "$checkout/aur"
git config user.name 'Alper Ortac'
git config user.email 'alportac@gmail.com'
git add PKGBUILD .SRCINFO LICENSE
if git diff --cached --quiet; then
  echo 'AUR is already current.'
  exit 0
fi
version=$(awk -F= '/^pkgver=/{print $2}' "$root/PKGBUILD")
release=$(awk -F= '/^pkgrel=/{print $2}' "$root/PKGBUILD")
git commit -m "Update localflow-bin to $version-$release"
git push origin HEAD:master
