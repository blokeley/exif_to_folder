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

    def test_not_dates(self):
        tests = (
            r'photos\n567590041_1431887_2516.jpg',
            (r'photos\2005\New York\232323232%7Ffp58=ot)2346=495=967=XROQDF)'
             r'23237;5 86978ot1lsi.jpg'),
        )

        for test in tests:
            with self.subTest(test=test):
                with self.assertRaises(ValueError):
                    result = sort_media.date_from_str(test)
                    print(f'ERROR: {test} returned {result}')


class TestIgnore(unittest.TestCase):

    def test_ignored(self):
        tests = (
            r'.Picasa3Temp',
            r'.Picasa3Temp_1',
            r'Picasa2',
            r'Picasa2Albums',
            r'something.json',
            r'path\Thumbs.db',
            r'sort_media.log',
            r'foo\bar',
        )

        for test in tests:
            with self.subTest(test=test):
                self.assertTrue(sort_media.ignore(test))

    def test_no_ignore(self):
        tests = (
            r'.foo\bar.jpg',
            r'.2017\11\file.mp4',
        )

        for test in tests:
            with self.subTest(test=test):
                self.assertFalse(sort_media.ignore(test))


if __name__ == '__main__':
    unittest.main()
