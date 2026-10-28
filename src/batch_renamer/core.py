"""Plan and safely execute deterministic batch renames."""
import re
import uuid
from dataclasses import dataclass
from pathlib import Path


class RenameError(ValueError):
    """An invalid or unsafe rename operation."""


@dataclass(frozen=True)
class Rename:
    source: Path
    destination: Path


def _validate_piece(value: str, label: str) -> None:
    if not value or value in {'.', '..'} or re.search(r'[<>:"/\\|?*\x00-\x1f]', value):
        raise RenameError(f'Invalid {label}: {value!r}')
    if value.endswith((' ', '.')):
        raise RenameError(f'Invalid {label}: {value!r}')


def plan(directory: Path, *, prefix: str = 'file', start: int = 1, width: int = 3,
         extension: str | None = None, find: str | None = None,
         replace: str = '') -> list[Rename]:
    directory = Path(directory)
    if not directory.is_dir() or directory.is_symlink():
        raise RenameError('Directory must be an existing non-symlink directory')
    _validate_piece(prefix, 'prefix')
    if start < 0 or not 1 <= width <= 12:
        raise RenameError('Start must be nonnegative and width must be 1..12')
    if find is not None and not find:
        raise RenameError('Find text cannot be empty')
    if extension is not None:
        extension = extension.lstrip('.').lower()
        if not extension or not extension.isalnum():
            raise RenameError('Invalid extension filter')
    files = sorted((p for p in directory.iterdir() if p.is_file() and not p.is_symlink()
                    and not p.name.startswith('.') and
                    (extension is None or p.suffix.lower() == '.' + extension)),
                   key=lambda p: (p.name.casefold(), p.name))
    result = []
    for index, source in enumerate(files, start):
        stem = source.stem
        if find is not None:
            stem = stem.replace(find, replace)
        # Pattern: prefix_number_originalstem.extension
        new_name = f'{prefix}_{index:0{width}d}_{stem}{source.suffix}'
        _validate_piece(new_name, 'resulting filename')
        destination = directory / new_name
        if destination != source:
            result.append(Rename(source, destination))
    _validate_plan(result)
    return result


def _validate_plan(renames: list[Rename]) -> None:
    sources = {r.source for r in renames}
    destinations = [r.destination for r in renames]
    if len(set(str(p).casefold() for p in destinations)) != len(destinations):
        raise RenameError('Multiple files would have the same destination')
    for rename in renames:
        if rename.destination.exists() and rename.destination not in sources:
            raise RenameError(f'Destination already exists: {rename.destination.name}')


def apply(renames: list[Rename]) -> int:
    """Rename via temporary filenames; best-effort rollback on failure."""
    _validate_plan(renames)
    for item in renames:
        if not item.source.is_file() or item.source.is_symlink():
            raise RenameError(f'Source changed: {item.source.name}')
        if item.destination.parent != item.source.parent:
            raise RenameError('Cross-directory renames are not supported')
    staged: list[tuple[Rename, Path]] = []
    completed: list[tuple[Rename, Path]] = []
    try:
        for item in renames:
            temp = item.source.parent / f'.batch-renamer-{uuid.uuid4().hex}.tmp'
            item.source.rename(temp)
            staged.append((item, temp))
        for item, temp in staged:
            if item.destination.exists():
                raise RenameError(f'Destination appeared: {item.destination.name}')
            temp.rename(item.destination)
            completed.append((item, temp))
    except Exception:
        for item, _ in reversed(completed):
            if item.destination.exists() and not item.source.exists():
                item.destination.rename(item.source)
        for item, temp in reversed(staged):
            if temp.exists() and not item.source.exists():
                temp.rename(item.source)
        raise
    return len(completed)
