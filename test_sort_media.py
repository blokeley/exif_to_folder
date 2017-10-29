"""Unit tests for the sort_medias module."""

import unittest

import sort_media


class TestDateFromFilename(unittest.TestCase):

    def test_dates(self):
        tests = (
            (('2016', '09'), '2016-09-23'),
            (('2013', '12'), '2013-12-03 12:23'),
            (('2013', '07'), '2013-07-21 16.19.33.jpg'),
            (('2013', '07'), 'IMG_20130730_111421.jpg'),
            (('2014', '10'), 'IMG_20141025_083751-edited.jpg'),
            (('2015', '08'), '2015-08-10 13.16.58.jpg'),
            (('2014', '08'), 'IMG-20140825-WA0003.jpg'),
            (('2012', '09'), '20120908-Oakley-013.jpg'),
            (('1995', '10'), 'IMG_19951025_083751-edited.jpg'),
            (('1989', '08'), '1989-08-10 13.16.58.jpg'),
            (('2001', '11'), '2001-11-02'),
            (('2011', '10'), 'root/2011-10-02/some/path'),
            (('2010', '11'), '2010:11:16 21:19:34'),
            (('2009', '03'), r'\2009\03\file.jpg'),
            (('2007', '05'), '/2007/05/file.jpg'),
            )

        for test in tests:
            with self.subTest(test=test):
                self.assertEqual(test[0], sort_media.date_from_str(test[1]))


if __name__ == '__main__':
    unittest.main()
