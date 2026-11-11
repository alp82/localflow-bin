import importlib.util
from pathlib import Path
import unittest
import io
import json
import tempfile
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('update', Path(__file__).resolve().parents[1] / 'scripts/update.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


def release(version='9.1.0'):
    name = f'localflow-{version}-x86_64.AppImage'
    return {'tag_name': f'v{version}', 'draft': False, 'prerelease': False,
            'assets': [{'name': name, 'browser_download_url':
                        f'https://github.com/radiumcoders/localflow/releases/download/v{version}/{name}'}]}


class ReleaseSelection(unittest.TestCase):
    def test_new_stable_release(self):
        self.assertEqual(update.select_release(release('10.0.0'), '9.0.0')[0], '10.0.0')

    def test_same_version_and_downgrades_are_noops(self):
        for version in ['9.0.0', '8.9.0']:
            self.assertIsNone(update.select_release(release(version), '9.0.0'))

    def test_incomplete_release_is_retried_without_changing_recipe(self):
        data = release()
        data['assets'] = []
        with self.assertRaises(ValueError):
            update.select_release(data, '9.0.0')

    def test_rejects_prerelease_and_draft(self):
        for field in ['draft', 'prerelease']:
            data = release()
            data[field] = True
            with self.assertRaises(ValueError):
                update.select_release(data, '9.0.0')

    def test_rejects_unexpected_asset_origin(self):
        data = release()
        data['assets'][0]['browser_download_url'] = 'https://example.com/replaced.tar.zst'
        with self.assertRaises(ValueError):
            update.select_release(data, '9.0.0')

    def test_rejects_shell_syntax_and_unsupported_version_formats(self):
        for version in ['9.1.0;echo bad', '9.1.0-rc1', '9.1', '$(echo bad)']:
            with self.assertRaises(ValueError):
                update.select_release(release(version), '9.0.0')


class RecipeUpdate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.recipe = self.root / 'PKGBUILD'
        self.original = (Path(__file__).resolve().parents[1] / 'PKGBUILD').read_text()
        self.recipe.write_text(self.original)
        self.release = release('10.0.0')
        self.release['assets'][0]['digest'] = 'sha256:' + 'a' * 64

    def run_update(self, hashes):
        with patch.object(update, 'ROOT', self.root), \
             patch.object(update, 'get', return_value=io.BytesIO(json.dumps(self.release).encode())), \
             patch.object(update, 'checksum', side_effect=hashes):
            update.main()

    def test_refreshes_version_release_and_both_checksums(self):
        self.recipe.write_text(self.original.replace('pkgrel=1', 'pkgrel=3'))
        self.run_update(['a' * 64, 'b' * 64])
        result = self.recipe.read_text()
        self.assertIn('pkgver=10.0.0\n', result)
        self.assertIn('pkgrel=1\n', result)
        self.assertIn("sha256sums=('" + 'a' * 64 + "'", result)
        self.assertIn("'" + 'b' * 64 + "')", result)
        self.assertIn('/v${pkgver}/README.md', result)

    def test_digest_mismatch_leaves_recipe_unchanged(self):
        with self.assertRaisesRegex(ValueError, 'digest'):
            self.run_update(['c' * 64])
        self.assertEqual(self.recipe.read_text(), self.original)

    def test_readme_download_failure_leaves_recipe_unchanged(self):
        with self.assertRaises(OSError):
            self.run_update(['a' * 64, OSError('download failed')])
        self.assertEqual(self.recipe.read_text(), self.original)

    def test_unexpected_checksum_layout_leaves_recipe_unchanged(self):
        original = self.original.replace('sha256sums=(', 'sha512sums=(')
        self.recipe.write_text(original)
        with self.assertRaisesRegex(ValueError, 'checksum layout'):
            self.run_update(['a' * 64, 'b' * 64])
        self.assertEqual(self.recipe.read_text(), original)


if __name__ == '__main__':
    unittest.main()
