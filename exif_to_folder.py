"""Copy or move images into year/month folders."""

import argparse
from datetime import date
import logging
import os
from os.path import join
import shutil

import piexif

__version__ = '1.1'

# http://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/datetimeoriginal.html
DATETIME_ORIGINAL = 36867
"""EXIF key for original date time of photo."""

LOGGING_FILENAME = str(date.today()) + ' exif_to_folder.log'


def main():
    args = parse_args()
    setup_logging(level=args.loglevel)
    logging.debug('Parsed args: ' + str(args))

    copy(args.src, args.dest, args.mode)

    print('Finished successfully')


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + __version__)

    msg = 'mode can be one of "move", "copy", "dryrun" (default)'
    parser.add_argument('-m', '--mode', default='dryrun', help=msg,
                        choices=('move', 'copy', 'dryrun'))

    msg = 'path of source folder.  Default is current folder.'
    parser.add_argument('-s', '--src', default=os.curdir, help=msg)

    msg = 'path of destination folder. Default is current folder.'
    parser.add_argument('-d', '--dest', default=os.curdir, help=msg)

    msg = 'logging level: DEBUG=10; INFO=20; WARNING=30; ERROR=40; FATAL=50'
    parser.add_argument('-l', '--loglevel', help=msg, default=20, type=int)

    return parser.parse_args()


def setup_logging(level=logging.INFO):
    """Set up logging."""
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove any existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # Create a file handler to log to a file
    fh = logging.FileHandler(LOGGING_FILENAME)
    fh.setLevel(level)
    logger.addHandler(fh)

    # Create a stream handler to log to the terminal
    sh = logging.StreamHandler()
    sh.setLevel(level)
    logger.addHandler(sh)

    fmt = '%(asctime)s %(levelname)-8s %(name)s %(message)s'
    formatter = logging.Formatter(fmt)

    for handler in logger.handlers:
        handler.setFormatter(formatter)


def copy(src, dest, mode='dryrun'):
    """Copy or move JPEG files from src to dest/year/month directories.
    src - source directory
    dest - root destination directory
    """
    jpegs_copied = 0
    jpegs_found = 0

    for root, dirs, files in os.walk(src):
        # Remove hidden directories
        for dirname in dirs:
            if dirname.startswith('.'):
                logging.debug('Not searching ' + join(root, dirname))
                dirs.remove(dirname)

        for fname in files:
            # Ignore every file except JPEGs
            if not (fname.endswith('.jpg') or fname.endswith('.JPG')):
                logging.info('Ignoring ' + join(root, fname))
                continue

            jpegs_found += 1
            fpath = join(root, fname)
            logging.debug('Found ' + fpath)

            try:
                exif = piexif.load(fpath)

            except ValueError:
                logging.exception('Could not read ' + fpath)
                continue

            try:
                year, month = parse_date(exif['Exif'][DATETIME_ORIGINAL])

            except KeyError:
                logging.exception('Photo date time data not found for ' +
                                  fpath)
                continue

            dest_dir = join(dest, year, month)

            # Do not do anything if file is already in the correct folder
            if os.path.isfile(join(dest_dir, year, month, fname)):
                logging.info('Already OK: ' + fpath)
                continue

            # If file is not in the correct folder, make the folder(s)
            if not mode == 'dryrun':
                try:
                    if not os.path.isdir(dest_dir):
                        os.makedirs(dest_dir)

                    else:
                        logging.debug('Folder already exists: ' + dest_dir)

                except OSError:
                    logging.exception('Cannot create {}.'.format(dest_dir))
                    continue

            try:
                if mode == 'copy':
                    shutil.copy2(fpath, join(dest_dir, fname))
                    logging.info('Copied {} to {}'.format(fpath, dest_dir))
                    jpegs_copied += 1

                elif mode == 'move':
                    shutil.move(fpath, join(dest_dir, fname))
                    logging.info('Moved {} to {}'.format(fpath, dest_dir))
                    jpegs_copied += 1

                else:
                    msg = 'Would have moved or copied {} to {}'
                    logging.info(msg.format(fpath, dest_dir))

            except OSError:
                logging.exception('Cannot copy or move file.')
                continue

    logging.info('Copied or moved {} out of {}'.format(
                    jpegs_copied, jpegs_found))


def parse_date(date_str):
    """Return the year and month as a tuple."""
    strng = date_str.decode()
    return strng[0:4], strng[5:7]


if __name__ == '__main__':
    main()
