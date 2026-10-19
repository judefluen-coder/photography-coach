"""Public archive portability and private-data boundaries; no private dataset needed."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'docs/archive/prototype-v0.1'


class RepositoryLayoutTest(unittest.TestCase):
    def test_current_entrypoints_and_archives_are_present(self) -> None:
        for name in ('SKILL.md', 'app/README.md', 'core/contracts.py', 'references/evaluation-standard.md',
                     'docs/demo/index.html', 'research/README.md', 'docs/versions.md',
                     'docs/archive/prototype-v0.1/RUN.md', 'docs/archive/prototype-v0.1/app.js'):
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).is_file())
        for version in ('0.2', '0.3', '0.4', '0.5', '0.6'):
            self.assertTrue((ROOT / f'research/archive/standards/photography-evaluation-standard-v{version}.md').is_file())

    def test_private_material_and_compatibility_aliases_are_ignored(self) -> None:
        paths = ['.local-data/private-photo.jpg', '.local-data/research/benchmark-202609/sealed/map.json',
                 '.local-data/migrations/before.json', '.benchmark-runs', '.benchmark-cache',
                 'docs/archive/photography-benchmark', 'docs/archive/prototype-v0.1/.npm-cache',
                 'docs/archive/prototype-v0.1/.pw-daemon', '.venv/private', '.env', '.env.local']
        result = subprocess.run(['git', 'check-ignore', '--no-index', '--stdin'], cwd=ROOT,
                                input='\n'.join(paths) + '\n', text=True, capture_output=True, check=True)
        self.assertEqual(set(result.stdout.splitlines()), set(paths))

    def test_git_index_contains_no_private_data_or_tool_cache(self) -> None:
        tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT, text=True).split('\0')
        forbidden = {'.local-data', '.benchmark-runs', '.benchmark-cache', '.npm-cache', '.pw-daemon', '.venv'}
        for name in filter(None, tracked):
            self.assertFalse(set(Path(name).parts) & forbidden, name)
            self.assertNotEqual(name, 'docs/archive/photography-benchmark')

    def test_new_public_archive_text_has_no_machine_specific_paths(self) -> None:
        paths = list((ROOT / 'research').rglob('*.md')) + list(ARCHIVE.glob('*.md'))
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotRegex(path.read_text(encoding='utf-8'), r'/Users/|/var/folders/|file:///')

    def test_public_archive_markdown_local_links_resolve(self) -> None:
        paths = list((ROOT / 'research').rglob('*.md')) + list((ROOT / 'docs/archive').glob('*.md'))
        paths += list(ARCHIVE.glob('*.md')) + [ROOT / 'docs/versions.md']
        for path in paths:
            for link in re.findall(r'\]\(([^)\s]+)\)', path.read_text(encoding='utf-8')):
                parsed = urlsplit(link)
                if parsed.scheme or not parsed.path:
                    continue
                with self.subTest(file=path.relative_to(ROOT), link=link):
                    self.assertFalse(parsed.path.startswith('/'), 'Public links must be portable')
                    self.assertTrue((path.parent / unquote(parsed.path)).is_file(), link)

    def test_legacy_image_dependencies_remain_explicitly_local(self) -> None:
        script = (ARCHIVE / 'app.js').read_text(encoding='utf-8')
        sources = re.findall(r'\bsrc: "([^"]+)"', script)
        self.assertEqual(len(sources), 6)
        for source in sources:
            self.assertTrue(source.startswith('../photography-benchmark/'), source)
        html = (ARCHIVE / 'index.html').read_text(encoding='utf-8')
        for link in re.findall(r'(?:src|href)="([^"]+)"', html):
            if link.startswith(('#', 'https:', 'http:', 'data:', '../photography-benchmark/')):
                continue
            self.assertTrue((ARCHIVE / link).is_file(), link)


if __name__ == '__main__':
    unittest.main()
