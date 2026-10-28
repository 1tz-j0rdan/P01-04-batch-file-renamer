# P01-04 — Batch File Renamer

A preview-first Python CLI for batch renaming files without overwriting existing files.

## Features
- Preview (dry run) by default; `--apply` is required to change files
- Configurable prefix, starting number, and zero-padding width
- Optional extension filter and find/replace in filename stems
- Deterministic alphabetical ordering
- Detects collisions and skips folders, hidden files, and symlinks
- Uses temporary names to safely handle renaming cycles, with best-effort rollback on errors
- Includes automated tests and GitHub Actions CI

## Setup (PowerShell)
```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Demo (use disposable sample files)
```powershell
New-Item -ItemType Directory -Force .\demo-files
Set-Content .\demo-files\photo.jpg "example"
Set-Content .\demo-files\notes.txt "example"
Set-Content .\demo-files\report.txt "example"
python -m batch_renamer .\demo-files --prefix archive --width 3
python -m batch_renamer .\demo-files --prefix archive --width 3 --apply
Get-ChildItem .\demo-files
```

Expected names: `archive_001_notes.txt`, `archive_002_photo.jpg`, `archive_003_report.txt`.

Filter by extension: `python -m batch_renamer .\demo-files --extension txt --prefix doc`

Find/replace original stem: `python -m batch_renamer .\demo-files --find report --replace summary`

## Tests and lint
```powershell
python -m pytest -v
python -m ruff check .
```

## Safety limitations
The tool does not recurse into subdirectories. It avoids overwriting known destinations, but cannot guarantee atomicity against external programs modifying files during execution. Rollback is best-effort and cannot recover from process termination or power loss. Use test folders or backups for important files.
