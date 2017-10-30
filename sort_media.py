"""Copy or move images into year/month folders."""

import argparse
from datetime import date
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

__version__ = '1.3'

# http://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/datetimeoriginal.html
DATETIME_ORIGINAL = 36867
"""EXIF key for original date time of photo."""

# Warn if year of file creation is unlikely
YEAR_MAX = date.today().year + 1
YEAR_MIN = 1945

IGNORED = (
    r'^Picasa2',
    r'^Picasa2Albums',
    r'^\.Picasa3Temp',
    r'\.ini$',
    r'\.db$',
    r'\.json$',
    r'\.log$',
    r'\.rss$',
    r'\.url$',
    r'\.pmp$',
    )
"""Sequence of folder and file names to ignore."""


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


def ignore(path: str, *, ignored: Sequence[str]=IGNORED) -> bool:
    """Return True if path should be ignored, False otherwise."""
    return any(re.search(pattern, path) for pattern in ignored)


def get_paths(src_dir: Path) -> Iterator[Path]:
    """Generate valid file paths under the src_dir directory."""
    logger = logging.getLogger('get_paths')

    for root, dirs, files in os.walk(src_dir):
        # Remove hidden directories
        for dirname in dirs:
            path = os.path.join(root, dirname)
            if ignore(path):
                logger.debug(f'Ignoring folder: {path}')
                dirs.remove(dirname)

        for fname in files:
            path = os.path.join(root, fname)
            if ignore(path):
                logger.debug(f'Ignoring file: {path}')
                continue

            yield Path(root, fname)


def date_from_exif(src_file: Path) -> Sequence[str]:
    """Get the date tuple (year, month) from JPEG EXIF data."""
    logger = logging.getLogger('date_from_exif')

    try:
        exif = piexif.load(str(src_file))
        return date_from_str(exif['Exif'][DATETIME_ORIGINAL].decode())

    except struct.error:
        logger.debug(f'struct.error parsing {src_file}')
        raise

    except KeyError:
        logger.debug(f'No date in EXIF for {src_file}')
        raise

    except ValueError as ex:
        ex_type = ex.__class__.__name__
        logger.debug(f'{ex_type}: {ex} when reading {src_file}')
        raise

    except Exception:
        logger.exception('Unexpected exception')
        raise


def date_from_str(text: str) -> Sequence[str]:
    """Get the date tuple (year, month) from the text string."""
    logger = logging.getLogger('date_from_str')

    # No leading digit, then 1 or 2 followed by 3 digits (for years 1ddd and
    # 2ddd), then any of -:\/ then 2 digits, then any of -:\/ then optional 2
    # digits, then no trailing digits
    pattern = r'(?<!\d)([12]\d{3})[-:\\/]?(\d{2})[-:\\/]?(?:\d{2})?(?!\d)'
    match = re.search(pattern, text)

    if match:
        return match.group(1, 2)

    else:
        msg = f'Could not find date in string "{text}"'
        logger.debug(msg)
        raise ValueError(msg)


def copy(src_file: Path, dest_dir: Path, mode: str='dryrun') -> None:
    """Copy or move file from src_file to dest directory.
    src_file - source filename
    dest_dir - destination directory
    """
    logger = logging.getLogger('copy')
    dest_file = dest_dir / src_file.name

    if src_file == dest_file:
        logger.debug(f'{src_file} already at {dest_file}')
        return

    # Warn if there is alrady a file in the destination
    if dest_file.is_file():
        logger.error(f'{src_file} already at {dest_file}')
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
            return

        elif mode == 'move':
            shutil.move(src_file, dest_file)
            logger.info(f'Moved {src_file} to {dest_file}')
            return

        else:
            msg = f'Would have moved or copied {src_file} to {dest_file}'
            logger.info(msg)
            return

    except OSError:
        logger.exception(f'Cannot copy or move {src_file} to {dest_file}')
        return


def main() -> int:
    setup_logging()
    args = parse_args()
    logger = logging.getLogger('main')

    for src_file in get_paths(args.src):
        try:
            # Try getting year and month from EXIF data
            year, month = date_from_exif(src_file)

        except Exception:
            try:
                # Try getting year and month from filename
                year, month = date_from_str(src_file.stem)

            except Exception:
                try:
                    # Try getting date from source folder name(s)
                    year, month = date_from_str(str(src_file.parent))

                except Exception:
                    logger.warning(f'Could not get date for {src_file}')
                    continue

        if YEAR_MAX < int(year) < YEAR_MIN:
            logger.warning(f'Year {year} found for {src_file}')

        dest_dir = args.dest / year / month
        copy(src_file, dest_dir, args.mode)

    logger.info('Finished successfully')
    return 0


if __name__ == '__main__':
    sys.exit(main())
