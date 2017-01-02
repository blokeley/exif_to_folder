"""Unit tests for the exif_to_folders module."""

import unittest

from exif_to_folder import parse_date, is_in_folder


class TestParseDates(unittest.TestCase):

    def test_parse(self):
        tests = (
            (('2016', '09'), b'2016-09-23'),
            (('2013', '12'), b'2013-12-03 12:23'),
            )

        for test in tests:
            with self.subTest(test=test):
                self.assertEqual(test[0], parse_date(test[1]))


class TestIsInFolder(unittest.TestCase):

    def test_is_in_folder(self):
        tests = (
            (True, 'dest/2016/09', 'dest', '2016', '09'),
            (False, '2015/09', 'dest', '2016', '09'),
            )

        for test in tests:
            with self.subTest(test=test):
                self.assertEqual(test[0], is_in_folder(*test[1:]))


if __name__ == '__main__':
    unittest.main()
