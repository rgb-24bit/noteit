# -*- coding: utf-8 -*-

import os
import re

from collections import namedtuple
from pathlib import Path
from typing import Union, TextIO


TITLE_MATCHER = re.compile(r'#\+TITLE:\s*(.+)')
EXCLUDE_DIR_NAMES = 'image', 'assets', 'static'
NOTE_SUFFIX = '.org'


Node = namedtuple('Node', ['path', 'name', 'subdirs', 'subnotes'])
Note = namedtuple('Note', ['path', 'name'])


def get_note_name(note: Path) -> str:
    """Get the name of the note."""
    with open(note, encoding='utf-8') as fp:
        match = TITLE_MATCHER.search(fp.readline())
        if match:
            return match.group(1)
        return note.stem


def make_vtree(basedir: Union[str, Path]) -> Node:
    """Building a virtual directory tree."""
    dirpath, subdirs, subnotes = Path(basedir), [], []

    # Need sorted directories and files
    for subitem in sorted(os.listdir(dirpath)):
        curr_path = Path(dirpath, subitem)
        if curr_path.is_dir() and curr_path.stem not in EXCLUDE_DIR_NAMES:
            subdir = make_vtree(curr_path)
            if len(subdir.subdirs) > 0 or len(subdir.subnotes) > 0:
                subdirs.append(make_vtree(curr_path))
        elif curr_path.suffix == NOTE_SUFFIX:
            subnotes.append(Note(curr_path, get_note_name(curr_path)))

    return Node(dirpath, dirpath.stem, subdirs, subnotes)


def makecatalog(fd: TextIO, notes: Node):
    """Generate content catalog."""
    fd.write('## Table of contents\n')

    itemfmt = '  + [{name}](#{anchor})\n'

    for item in notes.subdirs:
        fd.write(itemfmt.format(name=item.name, anchor=item.name.lower()))


def makecontent(fd: TextIO, notes: Node, level: int = 0):
    """Generate file specific content."""
    headfmt = '## {name}\n'
    typefmt = '  ' * level + '+ **{name}**\n'
    itemfmt = '  ' * level + '+ [{name}]({href})\n'

    for subdir in notes.subdirs:
        if level == 0:
            fd.write(headfmt.format(name=subdir.name))
        else:
            fd.write(typefmt.format(name=subdir.name))
        makecontent(fd, subdir, level + 1)

    for subnote in notes.subnotes:
        fd.write(itemfmt.format(name=subnote.name,
                                href=subnote.path.as_posix()))


def make(fn: str, basedir: str):
    """Generate note index."""
    notes = make_vtree(basedir)

    with open(fn, 'w', encoding='utf-8') as fd:
        makecatalog(fd, notes)
        makecontent(fd, notes)


if __name__ == '__main__':
    make('README.md', Path(os.path.abspath('.')).name)
