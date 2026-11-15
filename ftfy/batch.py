"""
Batch fixing of mojibake across a directory tree.

While :func:`ftfy.fix_text` handles a single string and :func:`ftfy.fix_file`
handles a single file, :func:`fix_tree` walks a whole directory recursively,
applies :func:`ftfy.fix_text` to every supported text file, and reports which
files would be changed.

By default (``apply=False``) this is a dry run: files are read and analyzed,
but nothing is written to disk. Pass ``apply=True`` to rewrite the files whose
content would change.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import NamedTuple

from ftfy import fix_text

#: File extensions that are treated as text and therefore scanned.
TEXT_SUFFIXES = (".txt", ".md", ".csv")


class FileChange(NamedTuple):
    """The fix status of a single file within a scanned tree."""

    #: Path of the file, relative to the scanned root, in POSIX form.
    path: str

    #: Whether :func:`ftfy.fix_text` produced different content.
    changed: bool


class TreeReport(NamedTuple):
    """Summary of a :func:`fix_tree` run."""

    #: Number of text files (matching `TEXT_SUFFIXES`) that were scanned.
    files_scanned: int

    #: Number of scanned files whose content differs after fixing.
    files_changed: int

    #: One `FileChange` per scanned file, in deterministic path order.
    details: list[FileChange]


def fix_tree(root: str | os.PathLike[str], apply: bool = False) -> TreeReport:
    """
    Recursively fix text files under ``root``.

    Only files with a ``.txt``, ``.md``, or ``.csv`` suffix are read; every
    other file (including binaries) is ignored and left out of the report.
    Each eligible file is decoded as UTF-8, passed through
    :func:`ftfy.fix_text`, and compared against its original content.

    When ``apply`` is False (the default), nothing is written. When ``apply``
    is True, files whose fixed content differs are rewritten in UTF-8.

    Returns a `TreeReport` with the number of files scanned, the number whose
    content would change (or did change, when applying), and per-file details
    whose paths are relative to ``root`` in POSIX form (for example
    ``sub/c.csv``).
    """
    root_path = Path(root)
    details: list[FileChange] = []

    for path in sorted(p for p in root_path.rglob("*") if p.is_file()):
        if path.suffix not in TEXT_SUFFIXES:
            continue

        original_bytes = path.read_bytes()
        original = original_bytes.decode("utf-8")
        fixed = fix_text(original)
        changed = fixed != original

        if changed and apply:
            path.write_bytes(fixed.encode("utf-8"))

        rel_path = path.relative_to(root_path).as_posix()
        details.append(FileChange(path=rel_path, changed=changed))

    files_changed = sum(1 for item in details if item.changed)
    return TreeReport(
        files_scanned=len(details),
        files_changed=files_changed,
        details=details,
    )
