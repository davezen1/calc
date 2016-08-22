from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

import xlrd

from .common import path
from ..spreadsheet_converter import Region10SpreadsheetConverter


R10_XLSX_PATH = path('static', 'data_capture', 'r10_export_sample.xlsx')


def r10_file(content=None, name='r10.xlsx'):
    if content is None:
        with open(R10_XLSX_PATH, 'rb') as f:
            content = f.read()

    if type(content) is str:
        content = bytes(content, 'UTF-8')

    return SimpleUploadedFile(name, content)


class TestRegion10SpreadsheetConverter(TestCase):
    '''Tests for Region10SpreadsheetConverter'''
    def test_is_valid_file(self):
        converter = Region10SpreadsheetConverter(xls_file=r10_file())
        self.assertTrue(converter.is_valid_file())

        converter.xl_heading_to_csv_idx_map = {'Location': 0}
        self.assertTrue(converter.is_valid_file())

        converter.xl_heading_to_csv_idx_map = {'bad_col': 0}
        self.assertFalse(converter.is_valid_file())

        converter = Region10SpreadsheetConverter(xls_file=r10_file('blah'))
        self.assertFalse(converter.is_valid_file())

    def test_get_metadata(self):
        converter = Region10SpreadsheetConverter(xls_file=r10_file())
        book = xlrd.open_workbook(file_contents=r10_file().read())
        sheet = book.sheet_by_index(0)
        expected = {
            'num_rows': sheet.nrows - 1
        }
        self.assertEqual(expected, converter.get_metadata())

    def test_get_heading_indices_map(self):
        converter = Region10SpreadsheetConverter(xls_file=r10_file())
        indices_map = converter.get_heading_indices_map()

        expected = {
            'Year 1/base': 1,
            'Contract Year': 17,
            'CONTRACT .': 11,
            'Year 3': 3,
            'Schedule': 12,
            'MinExpAct': 7,
            'Location': 9,
            'Begin Date': 14,
            'COMPANY NAME': 10,
            'SIN NUMBER': 13,
            'Labor Category': 0,
            'Year 2': 2,
            'Year 5': 5,
            'Education': 6,
            'End Date': 15,
            'Year 4': 4,
            'Bus Size': 8
        }
        self.assertEqual(expected, indices_map)

    def test_get_heading_indices_map_raises(self):
        converter = Region10SpreadsheetConverter(xls_file=r10_file())
        converter.xl_heading_to_csv_idx_map = {'blah': 0}
        with self.assertRaises(ValueError):
            converter.get_heading_indices_map(raises=True)

    def test_convert_next(self):
        count = 0
        converter = Region10SpreadsheetConverter(xls_file=r10_file())
        for row in converter.convert_next():
            count += 1
            self.assertEqual(len(row),
                             len(converter.xl_heading_to_csv_idx_map))

        self.assertEqual(count, 3)

    def test_convert_file(self):
        converter = Region10SpreadsheetConverter(xls_file=r10_file())
        parsed_rows = converter.convert_file()
        self.assertEqual(len(parsed_rows), 3)
