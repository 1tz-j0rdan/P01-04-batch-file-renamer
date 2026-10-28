"""Command-line interface for batch renaming."""

import argparse
from pathlib import Path

from .core import RenameError, apply, plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Safely preview and batch-rename files.')
    parser.add_argument('directory', type=Path)
    parser.add_argument('--prefix', default='file')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--width', type=int, default=3)
    parser.add_argument('--extension', help='Only rename this extension, e.g. jpg')
    parser.add_argument('--find', help='Text to replace within original filename stems')
    parser.add_argument('--replace', default='')
    parser.add_argument('--apply', action='store_true', help='Perform renames (default: preview)')
    args = parser.parse_args(argv)
    try:
        operations = plan(args.directory, prefix=args.prefix, start=args.start,
                          width=args.width, extension=args.extension,
                          find=args.find, replace=args.replace)
        print(f'{"Applying" if args.apply else "Previewing"} {len(operations)} rename(s):')
        for item in operations:
            print(f'  {item.source.name} -> {item.destination.name}')
        if args.apply:
            print(f'Renamed {apply(operations)} file(s).')
        else:
            print('Preview only. Add --apply to rename files.')
        return 0
    except (RenameError, OSError) as exc:
        parser.exit(2, f'Error: {exc}\n')
