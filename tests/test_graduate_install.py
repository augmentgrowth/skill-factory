"""Bounded install regressions: python3 -m unittest discover -s tests -p test_graduate_install.py."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / '.claude/skills/graduate-skill/scripts/install_skill.py'
spec = importlib.util.spec_from_file_location('install_skill', SCRIPT)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'build home'
        self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.source = self.repo / 'skill'
        self.source.mkdir()
        self.destination = self.root / 'personal skills' / 'skill'
        self.write('SKILL.md', '# Example')
        self.write('config.json', '{"shared": 1}')
        self.write('assets/config.json', '{"nested": 1}')
        self.write('personal/config.json', '{"personal": 1}')
        self.write('untracked/config.json', '{"untracked": 1}')
        self.write('.env', 'private')
        self.write('assets/.env', 'nested private')
        self.write('ordinary.txt', 'old')
        self.write('.gitignore', 'personal/config.json\n.env\n')
        subprocess.run(['git', '-C', str(self.repo), 'add', 'skill/SKILL.md', 'skill/config.json',
                        'skill/assets/config.json', 'skill/ordinary.txt', 'skill/.gitignore'], check=True)

    def write(self, relative, text):
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_shared_first_install_and_personal_reinstall(self):
        installer.install(self.source, self.destination)
        self.assertEqual((self.destination / 'config.json').read_text(), '{"shared": 1}')
        self.assertEqual((self.destination / 'assets/config.json').read_text(), '{"nested": 1}')
        for path in ('personal/config.json', 'untracked/config.json', '.env', 'assets/.env'):
            self.assertFalse((self.destination / path).exists())
        (self.destination / 'config.json').write_text('user setting')
        (self.destination / 'assets/config.json').write_text('nested user setting')
        (self.destination / '.env').write_text('user secret')
        (self.destination / 'assets/.env').write_text('nested user secret')
        (self.destination / 'stale.txt').write_text('stale')
        self.write('config.json', 'changed upstream')
        self.write('ordinary.txt', 'new')
        installer.install(self.source, self.destination)
        self.assertEqual((self.destination / 'config.json').read_text(), 'user setting')
        self.assertEqual((self.destination / 'assets/config.json').read_text(), 'nested user setting')
        self.assertEqual((self.destination / '.env').read_text(), 'user secret')
        self.assertEqual((self.destination / 'assets/.env').read_text(), 'nested user secret')
        self.assertEqual((self.destination / 'ordinary.txt').read_text(), 'new')
        self.assertFalse((self.destination / 'stale.txt').exists())

    def test_standalone_skill_repository_does_not_copy_git_metadata(self):
        (self.repo / 'SKILL.md').write_text('# Standalone skill')
        installer.install(self.repo, self.destination)
        self.assertFalse((self.destination / '.git').exists())

    def test_tracked_but_ignored_config_is_personal(self):
        self.write('.gitignore', 'config.json\n.env\n')
        installer.install(self.source, self.destination)
        self.assertFalse((self.destination / 'config.json').exists())
        self.assertFalse((self.destination / 'assets/config.json').exists())

    def test_parent_traversal_rejected(self):
        with self.assertRaises(ValueError):
            installer.install(self.source, self.root / 'link' / '..' / 'install')

    def test_overlap_rejected(self):
        for destination in (self.source, self.source / 'installed', self.repo):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                installer.install(self.source, destination)

    def test_source_link_and_destination_ancestor_link_rejected(self):
        (self.source / 'unsafe').symlink_to(self.root)
        with self.assertRaises(ValueError):
            installer.install(self.source, self.destination)
        (self.source / 'unsafe').unlink()
        (self.root / 'link').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            installer.install(self.source, self.root / 'link' / 'install')
        self.assertFalse(self.destination.exists())

    def test_destination_link_rejected_before_mutation(self):
        self.destination.mkdir(parents=True)
        (self.destination / 'ordinary.txt').write_text('keep')
        (self.destination / 'config.json').symlink_to(self.source / 'config.json')
        with self.assertRaises(ValueError):
            installer.install(self.source, self.destination)
        self.assertEqual((self.destination / 'ordinary.txt').read_text(), 'keep')

    def test_settings_parent_conflict_rejected_before_mutation(self):
        self.destination.mkdir(parents=True)
        (self.destination / 'private').mkdir()
        (self.destination / 'private/config.json').write_text('user setting')
        self.write('private', 'would replace directory')
        with self.assertRaises(ValueError):
            installer.install(self.source, self.destination)
        self.assertEqual((self.destination / 'private/config.json').read_text(), 'user setting')


if __name__ == '__main__':
    unittest.main()
