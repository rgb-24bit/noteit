# -*- coding: utf-8 -*-

import os
import re

from pathlib import Path
from typing import List, Tuple, Dict, Generator


EXCLUDE_DIR = 'image', 'assets', 'static'
NOTE_FILE_SUFFIX = '.org'


def make_walker(basedir: str) -> Generator[Tuple[Path, List[Path], List[Path]], None, None]:
    """Simple directory file walker."""
    dirpath, subdirs, subfiles = Path(basedir), [], []

    # Sorted directories and files
    for subitem in sorted(os.listdir(dirpath)):
        curr_path = Path(dirpath, subitem)
        if curr_path.is_dir():
            subdirs.append(curr_path)
        else:
            subfiles.append(curr_path)

    yield dirpath, subdirs, subfiles

    for subdir in subdirs:
        yield from make_walker(subdir.as_posix())


def get_note_name(note):
    """Get the name of the note."""
    with open(note, encoding='utf-8') as fp:
        match = re.search(r'#\+TITLE:\s*(.+)', fp.readline())
        if match:
            return match.group(1)
    return Path(note).stem


def walk(walker: Generator[Tuple[Path, List[Path], List[Path]], None, None]) -> List:
    """Traverse the specified directory to get the note files in it."""
    try:
        dirpath, subdirs, subfiles = next(walker)

        notes = []

        for subdir in subdirs:
            subnotes = walk(walker)
            if not (subdir.name in EXCLUDE_DIR or len(subnotes) == 0):
                notes.append({subdir.name: subnotes})

        for subfile in subfiles:
            if subfile.suffix == NOTE_FILE_SUFFIX:
                notes.append(subfile.as_posix())

        return notes
    except StopIteration:
        pass


def makecatalog(fd, notes, level=1):
    """Generate file content directory."""
    itemfmt = '  ' * level + '+ [{name}](#{anchor})\n'

    for subnotes in notes:
        if not isinstance(subnotes, dict):
            break
        name = next(iter(subnotes))
        fd.write(itemfmt.format(name=name, anchor=name.lower()))


def makecontent(fd, notes, level=0):
    """Generate file specific content."""
    headfmt = '## {name}\n'
    typefmt = '  ' * level + '+ **{name}**\n'
    itemfmt = '  ' * level + '+ [{name}]({href})\n'

    for subnotes in notes:
        if isinstance(subnotes, dict):
            name = next(iter(subnotes))
            if level == 0:
                fd.write(headfmt.format(name=name))
            else:
                fd.write(typefmt.format(name=name))
            makecontent(fd, subnotes[name], level + 1)
        else:
            fd.write(itemfmt.format(name=get_note_name(subnotes), href=subnotes))


def make(fn, basedir):
    """Generate note index."""
    notes = walk(make_walker(basedir))

    with open(fn, 'w', encoding='utf-8') as fd:
        fd.write('## Table of contents\n')
        makecatalog(fd, notes)
        makecontent(fd, notes)


if __name__ == '__main__':
    make('README.md', 'noteit')
