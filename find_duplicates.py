"""Find duplicate filenames in dest_dir.

If src_dir is specified, say if filenames in src_dir are NOT in dest_dir.
"""

import argparse
from collections import defaultdict
import logging
import os
from pathlib import Path
import sys
from typing import DefaultDict, List

from sort_media import get_paths, setup_logging

__version__ = '0.1'


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + __version__)

    msg = 'path of source directory.'
    parser.add_argument('-s', '--src', default=None,
                        type=Path, help=msg)

    msg = 'path of destination directory. Default is current directory.'
    parser.add_argument('-d', '--dest', default=os.curdir,
                        type=Path, help=msg)

    args = parser.parse_args()

    if not args.dest.is_dir():
        raise argparse.ArgumentError(f'{args.dest} is not a directory.')

    return args


def main() -> int:
    setup_logging()
    args = parse_args()
    logger = logging.getLogger('main')

    name_to_dirs = defaultdict(list)  # type: DefaultDict[str, List[Path]]
    """Map of filename to list of directories in which filename was found."""

    # Walk the directory tree adding directories to filename keys
    for path in get_paths(args.dest):
        name_to_dirs[path.name].append(path.parent)

    for name, dirs in name_to_dirs.items():
        # If the filename was found in more than 1 directory, warn as
        # possible duplicate
        if len(dirs) > 1:
            logger.warning(f'{name} found in f{dirs}')

    if args.src:
        for path in get_paths(args.src):
            if path.name not in name_to_dirs:
                logger.info(f'{path.name} NOT found in {args.dest}')

    logger.info('Finished successfully')
    return 0


if __name__ == '__main__':
    sys.exit(main())
