from pathlib import Path

import pytest

from batch_renamer import RenameError, apply, plan
from batch_renamer.cli import main


def make(directory: Path, *names: str) -> None:
    for name in names:
        (directory / name).write_text(name)


def test_preview_does_not_change_files(tmp_path):
    make(tmp_path, 'b.txt', 'a.jpg')
    items = plan(tmp_path, prefix='new')
    assert [i.destination.name for i in items] == ['new_001_a.jpg', 'new_002_b.txt']
    assert (tmp_path / 'b.txt').exists()


def test_apply(tmp_path):
    make(tmp_path, 'b.txt', 'a.jpg')
    assert apply(plan(tmp_path, prefix='new')) == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == ['new_001_a.jpg', 'new_002_b.txt']


def test_extension_filter(tmp_path):
    make(tmp_path, 'a.JPG', 'b.txt')
    items = plan(tmp_path, extension='.jpg')
    assert len(items) == 1
    assert items[0].source.name == 'a.JPG'


def test_start_and_width(tmp_path):
    make(tmp_path, 'x.txt')
    assert plan(tmp_path, start=42, width=5)[0].destination.name == 'file_00042_x.txt'


def test_find_replace(tmp_path):
    make(tmp_path, 'draft_report.txt')
    assert (
    plan(tmp_path, find='draft', replace='final')[0].destination.name
    == 'file_001_final_report.txt'
)


@pytest.mark.parametrize('kwargs', [
    {'prefix': '../evil'}, {'prefix': ''}, {'prefix': 'bad:name'},
    {'width': 0}, {'width': 13}, {'start': -1}, {'extension': 'a/b'}, {'find': ''},
])
def test_bad_arguments(tmp_path, kwargs):
    with pytest.raises(RenameError):
        plan(tmp_path, **kwargs)


def test_invalid_directory(tmp_path):
    with pytest.raises(RenameError):
        plan(tmp_path / 'missing')


def test_existing_destination_directory(tmp_path):
    make(tmp_path, 'a.txt')
    (tmp_path / 'new_001_a.txt').mkdir()
    with pytest.raises(RenameError):
        plan(tmp_path, prefix='new')


def test_hidden_and_subfolders_skipped(tmp_path):
    make(tmp_path, '.secret', 'visible.txt')
    (tmp_path / 'folder').mkdir()
    assert [x.source.name for x in plan(tmp_path)] == ['visible.txt']


def test_empty_directory(tmp_path):
    assert plan(tmp_path) == []
    assert apply([]) == 0


def test_cli_preview_then_apply(tmp_path, capsys):
    make(tmp_path, 'a.txt')
    assert main([str(tmp_path), '--prefix', 'doc']) == 0
    assert (tmp_path / 'a.txt').exists()
    assert 'Preview only' in capsys.readouterr().out
    assert main([str(tmp_path), '--prefix', 'doc', '--apply']) == 0
    assert (tmp_path / 'doc_001_a.txt').exists()


def test_symlink_skipped(tmp_path):
    make(tmp_path, 'a.txt')
    link = tmp_path / 'link.txt'
    try:
        link.symlink_to(tmp_path / 'a.txt')
    except (OSError, NotImplementedError):
        pytest.skip('Symlinks unavailable')
    assert len(plan(tmp_path)) == 1


def test_second_run_renames_again(tmp_path):
    make(tmp_path, 'a.txt')
    apply(plan(tmp_path, prefix='x'))
    assert plan(tmp_path, prefix='x')[0].destination.name == 'x_001_x_001_a.txt'
