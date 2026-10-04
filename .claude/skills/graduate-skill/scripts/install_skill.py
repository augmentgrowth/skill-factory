#!/usr/bin/env python3
"""Install a skill while retaining personal settings. Python 3 stdlib; git and rsync required."""
import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys


def checked_tree(root: Path) -> None:
    """Reject links and special files before rsync can traverse or replace them."""
    for path in (root, *root.parents):
        if path.is_symlink():
            raise ValueError('Installation paths must not contain symbolic links.')
    if not root.exists():
        return
    if not root.is_dir():
        raise ValueError('Installation roots must be directories.')
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError('Skill trees must contain only ordinary files and directories.')
            if name in ('.env', 'config.json') and not stat.S_ISREG(mode):
                raise ValueError('Personal settings must be ordinary files.')


def install(source: Path, destination: Path) -> None:
    if '..' in source.parts or '..' in destination.parts:
        raise ValueError('Use canonical paths without parent-directory traversal.')
    source = Path(os.path.abspath(source))
    destination = Path(os.path.abspath(destination))
    checked_tree(source)
    checked_tree(destination)
    if not source.is_dir() or not (source / 'SKILL.md').is_file():
        raise ValueError('Source must be a skill folder containing SKILL.md.')
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError('Source and destination must not overlap.')
    if not shutil.which('git') or not shutil.which('rsync'):
        raise ValueError('Install git and rsync before graduating a skill.')
    # One batched index read and one ignore check, never a git call per file.
    tracked = subprocess.run(['git', '-C', str(source), 'ls-files', '-z', '--', '.'],
                             check=True, capture_output=True).stdout.split(b'\0')
    configs = [os.fsdecode(path) for path in tracked
               if path and Path(os.fsdecode(path)).name == 'config.json']
    ignored = set()
    if configs:
        result = subprocess.run(['git', '-C', str(source), 'check-ignore', '--no-index', '-z', '--stdin'],
                                input=b'\0'.join(os.fsencode(p) for p in configs) + b'\0',
                                capture_output=True)
        if result.returncode not in (0, 1):
            raise ValueError('Could not determine whether configuration is personal.')
        ignored = {os.fsdecode(p) for p in result.stdout.split(b'\0') if p}
    shared = [Path(p) for p in configs if p not in ignored and (source / p).is_file()]
    # Detect file/directory clashes for protected settings before ordinary files change.
    for directory, _, files in os.walk(destination) if destination.exists() else []:
        for name in files:
            relative = (Path(directory) / name).relative_to(destination)
            if name in ('.env', 'config.json'):
                for parent in relative.parents:
                    if parent != Path('.') and (source / parent).exists() and not (source / parent).is_dir():
                        raise ValueError('Source conflicts with an installed settings directory.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['rsync', '-a', '--checksum', '--delete', '--exclude', '.env', '--exclude', 'config.json', '--exclude', '.git',
                    str(source) + '/', str(destination) + '/'], check=True, capture_output=True)
    for relative in shared:
        target = destination / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with (source / relative).open('rb') as incoming, target.open('xb') as outgoing:
                shutil.copyfileobj(incoming, outgoing)
            shutil.copystat(source / relative, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    try:
        install(args.source, args.destination)
    except (ValueError, OSError, subprocess.CalledProcessError):
        print('Installation stopped: check prerequisites and ordinary, separate skill paths.', file=sys.stderr)
        return 1
    print('Skill installed; existing personal settings retained.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
