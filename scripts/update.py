#!/usr/bin/env python3
"""Pin a newer stable upstream release; never evaluate release metadata as shell."""
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
API = 'https://api.github.com/repos/radiumcoders/localflow/releases/latest'


def version_tuple(version):
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
        raise ValueError(f'Unsupported release version: {version!r}; review manually')
    return tuple(map(int, version.split('.')))


def get(url, *, authenticated=False):
    headers = {'User-Agent': 'localflow-bin-release-check'}
    if authenticated and os.environ.get('GH_TOKEN'):
        headers['Authorization'] = f'Bearer {os.environ["GH_TOKEN"]}'
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120)


def checksum(url):
    digest = hashlib.sha256()
    with get(url) as response:
        for chunk in iter(lambda: response.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def select_release(release, current):
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Refusing draft or prerelease')
    tag = release['tag_name']
    if not tag.startswith('v'):
        raise ValueError('Expected a v-prefixed upstream tag')
    version = tag[1:]
    if version_tuple(version) <= version_tuple(current):
        return None
    name = f'localflow-{version}-x86_64.AppImage'
    assets = [a for a in release['assets'] if a['name'] == name]
    if len(assets) != 1:
        raise ValueError(f'Expected exactly one {name} asset; retry when release is complete')
    asset = assets[0]
    expected = f'https://github.com/radiumcoders/localflow/releases/download/{tag}/{name}'
    if asset['browser_download_url'] != expected:
        raise ValueError('Unexpected asset download URL')
    return version, asset


def main():
    path = ROOT / 'PKGBUILD'
    recipe = path.read_text()
    current = re.search(r'^pkgver=(.+)$', recipe, re.M).group(1)
    with get(API, authenticated=True) as response:
        release = json.load(response)
    selected = select_release(release, current)
    if selected is None:
        print(f'Already current: {current}')
        return
    version, asset = selected
    archive_hash = checksum(asset['browser_download_url'])
    if asset.get('digest') and asset['digest'] != f'sha256:{archive_hash}':
        raise ValueError('Downloaded archive does not match GitHub asset digest')
    readme_hash = checksum(f'https://raw.githubusercontent.com/radiumcoders/localflow/v{version}/README.md')
    recipe = re.sub(r'^pkgver=.+$', f'pkgver={version}', recipe, flags=re.M)
    recipe = re.sub(r'^pkgrel=.+$', 'pkgrel=1', recipe, flags=re.M)
    recipe, count = re.subn(r"sha256sums=\('[0-9a-f]{64}'\s+'[0-9a-f]{64}'\)",
                           f"sha256sums=('{archive_hash}'\n            '{readme_hash}')", recipe)
    if count != 1:
        raise ValueError('Unexpected checksum layout; refusing to edit')
    path.write_text(recipe)
    print(f'Updated {current} -> {version}; run scripts/check.sh --refresh-srcinfo')


if __name__ == '__main__':
    main()
