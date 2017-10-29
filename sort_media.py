"""Copy or move images into year/month folders."""

import argparse
import json
import logging
import logging.config
import os
from pathlib import Path
import re
import shutil
import struct
import sys
from typing import Iterator, Sequence

import piexif

__version__ = '1.2'

# http://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/datetimeoriginal.html
DATETIME_ORIGINAL = 36867
"""EXIF key for original date time of photo."""

IGNORED = (
    re.compile(r'\.picasa\.ini$'),
    re.compile(r'\.log$'),
    re.compile(r'\.json$'),
    )
"""Sequence of file names to ignore."""


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + __version__)

    msg = 'mode can be one of "move", "copy", "dryrun" (default)'
    parser.add_argument('-m', '--mode', default='dryrun', help=msg,
                        choices=('move', 'copy', 'dryrun'))

    msg = 'path of source folder.  Default is current folder.'
    parser.add_argument('-s', '--src', default=os.curdir,
                        type=Path, help=msg)

    msg = 'path of destination folder. Default is current folder.'
    parser.add_argument('-d', '--dest', default=os.curdir,
                        type=Path, help=msg)

    return parser.parse_args()


def setup_logging() -> None:
    """Use logging config from JSON dictionary in logging_config.json or
    default to simple terminal logging.
    """

    try:
        with open('logging_config.json') as f:
            logging.config.dictConfig(json.load(f))

    except FileNotFoundError:
        debug = logging.INFO
        fmt = r'%(asctime)s %(levelname)-8s %(message)s'
        logging.basicConfig(level=debug, format=fmt, datefmt='%H:%M:%S')


def get_paths(src_dir: Path) -> Iterator[Path]:
    """Generate valid file paths under the src_dir directory."""
    logger = logging.getLogger('get_paths')
    for root, dirs, files in os.walk(src_dir):
        # Remove hidden directories
        for dirname in dirs:
            if dirname.startswith('.'):
                logger.debug('Not searching ' + os.path.join(root, dirname))
                dirs.remove(dirname)

        for fname in files:
            yield Path(root, fname)


def date_from_exif(src_file: Path) -> Sequence[str]:
    """Get the date tuple (year, month) from JPEG EXIF data."""
    logger = logging.getLogger('date_from_exif')

    try:
        exif = piexif.load(str(src_file))
        return date_from_str(exif['Exif'][DATETIME_ORIGINAL].decode())

    except struct.error:
        logger.exception(f'struct.error parsing {src_file}')
        raise

    except ValueError as ex:
        logger.debug(f'ValueError {ex} when reading {src_file}')
        raise

    except KeyError:
        logger.debug(f'EXIF date not found in {src_file}')
        raise


def date_from_str(text: str) -> Sequence[str]:
    """Get the date tuple (year, month) from the text string."""
    logger = logging.getLogger('date_from_str')

    # Match 4 digits, then any of -:\/ then 2 digits
    match = re.search(r'(\d{4})[-:\\/]?(\d{2})', text)

    if match:
        return match.group(1, 2)

    else:
        msg = f'Could not find date in string {text}'
        logger.debug(msg)
        raise ValueError(msg)


def copy(src_file: Path, dest_dir: Path, mode: str='dryrun') -> None:
    """Copy or move file from src_file to dest directory.
    src_file - source filename
    dest_dir - destination directory
    """
    logger = logging.getLogger('copy')
    dest_file = dest_dir / src_file.name
    # Do not do anything if file is already in the correct folder
    if dest_file.is_file():
        logger.warning(f'File exists: {dest_file}')
        return

    # If file is not in the correct folder, make the folder(s)
    if not mode == 'dryrun':
        try:
            dest_file.mkdir(parents=True, exist_ok=True)

        except OSError:
            logger.exception(f'Cannot create {dest_dir}')
            return

    try:
        if mode == 'copy':
            shutil.copy2(src_file, dest_file)
            logger.info(f'Copied {src_file} to {dest_file}')

        elif mode == 'move':
            shutil.move(src_file, dest_file)
            logger.info(f'Moved {src_file} to {dest_file}')

        else:
            msg = f'Would have moved or copied {src_file} to {dest_file}'
            logger.info(msg)

    except OSError:
        logger.exception(f'Cannot copy or move {src_file} to {dest_file}')
        return


def main() -> int:
    setup_logging()
    args = parse_args()
    logger = logging.getLogger('main')

    for src_file in get_paths(args.src):

        if any(regex.search(str(src_file)) for regex in IGNORED):
            logger.debug(f'Ignoring {src_file}')
            continue

        try:
            # Try getting year and month from EXIF data
            year, month = date_from_exif(src_file)

        except Exception:
            try:
                # Try getting year and month from filename
                year, month = date_from_str(src_file.stem)

            except Exception:
                try:
                    # Try getting date from source directory name
                    year, month = date_from_str(str(src_file.parent))

                except Exception:
                    logger.warning(f'Could not get date for {src_file}')
                    continue

        dest_dir = args.dest / year / month
        copy(src_file, dest_dir, args.mode)

    logger.info('Finished successfully')
    return 0


if __name__ == '__main__':
    sys.exit(main())
