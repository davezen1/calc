import json
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from .common import path
from .test_models import ModelTestCase
from ..schedules import s70, registry
from contracts.loaders.region_10 import FEDERAL_MIN_CONTRACT_RATE


S70 = '%s.Schedule70PriceList' % s70.__name__

S70_XLSX_PATH = path('static', 'data_capture', 's70_example.xlsx')

XLSX_CONTENT_TYPE = ('application/vnd.openxmlformats-'
                     'officedocument.spreadsheetml.sheet')


def uploaded_xlsx_file(content=None):
    if content is None:
        with open(S70_XLSX_PATH, 'rb') as f:
            content = f.read()

    return SimpleUploadedFile(
        'foo.xlsx',
        content,
        content_type=XLSX_CONTENT_TYPE
    )


class SafeCellStrValueTests(TestCase):
    def test_cell_value_index_errors_are_ignored(self):
        s = MagicMock()
        s.cell_value.side_effect = IndexError()

        self.assertEqual(s70.safe_cell_str_value(s, 99, 99), '')
        self.assertEqual(s.cell_value.call_count, 1)

    def test_coercer_value_errors_are_ignored(self):
        s = MagicMock()
        s.cell_value.return_value = 'blah'

        c = Mock()
        c.side_effect = ValueError()

        self.assertEqual(s70.safe_cell_str_value(s, 99, 99, c), 'blah')
        self.assertEqual(s.cell_value.call_count, 1)
        self.assertEqual(c.call_count, 1)

    def test_result_is_stringified(self):
        s = MagicMock()
        s.cell_value.return_value = 5

        self.assertEqual(s70.safe_cell_str_value(s, 1, 1), '5')

    def test_coercer_is_used(self):
        s = MagicMock()
        s.cell_value.return_value = 5.0

        self.assertEqual(s70.safe_cell_str_value(s, 1, 1, int), '5')


class GleanLaborCategoriesTests(TestCase):
    def test_rows_are_returned(self):
        rows = s70.glean_labor_categories_from_file(uploaded_xlsx_file())
        self.assertEqual(rows, [{
            'sin': '132-51',
            'labor_category': 'Project Manager',
            'education_level': 'Bachelors',
            'min_years_experience': '5',
            'commercial_list_price': '125.0',
            'unit_of_issue': 'Hour',
            'most_favored_customer': 'All Commercial Customers',
            'best_discount': '0.07',
            'mfc_price': '123.99',
            'gsa_discount': '0.1',
            'price_excluding_iff': '110.99',
            'price_including_iff': '115.99',
            'volume_discount': '0.15',
        }])

    def test_validation_error_raised_when_sheet_not_present(self):
        with self.assertRaisesRegexp(
            ValidationError,
            r'There is no sheet in the workbook called "foo"'
        ):
            s70.glean_labor_categories_from_file(
                uploaded_xlsx_file(),
                sheet_name='foo'
            )


class LoadFromUploadValidationErrorTests(TestCase):
    @patch.object(s70, 'glean_labor_categories_from_file')
    def test_reraises_validation_errors(self, m):
        m.side_effect = ValidationError('foo')

        with self.assertRaisesRegexp(ValidationError, r'foo'):
            s70.Schedule70PriceList.load_from_upload(uploaded_xlsx_file())

    def test_raises_validation_error_on_corrupt_files(self):
        f = uploaded_xlsx_file(b'foo')

        with self.assertRaisesRegexp(
            ValidationError,
            r'An error occurred when reading your Excel data.'
        ):
            s70.Schedule70PriceList.load_from_upload(f)


@override_settings(DATA_CAPTURE_SCHEDULES=[S70])
class S70Tests(ModelTestCase):
    DEFAULT_SCHEDULE = S70

    def test_valid_rows_are_populated(self):
        p = s70.Schedule70PriceList.load_from_upload(uploaded_xlsx_file())

        self.assertEqual(len(p.valid_rows), 1)
        self.assertEqual(p.invalid_rows, [])

        self.assertEqual(p.valid_rows[0].cleaned_data, {
            'education_level': 'Bachelors',
            'labor_category': 'Project Manager',
            'min_years_experience': 5,
            'price_including_iff': Decimal('115.99'),
            'sin': '132-51'
        })

    def test_education_level_is_validated(self):
        p = s70.Schedule70PriceList(rows=[{'education_level': 'Batchelorz'}])

        self.assertRegexpMatches(
            p.invalid_rows[0].errors['education_level'][0],
            r'This field must contain one of the following values'
        )

    def test_min_years_experience_is_validated(self):
        p = s70.Schedule70PriceList(rows=[{'min_years_experience': ''}])

        self.assertEqual(p.invalid_rows[0].errors['min_years_experience'],
                         ['This field is required.'])

    def test_add_to_price_list_works(self):
        s = s70.Schedule70PriceList.load_from_upload(uploaded_xlsx_file())

        p = self.create_price_list()
        p.save()

        s.add_to_price_list(p)

        row = p.rows.all()[0]

        self.assertEqual(row.labor_category, 'Project Manager')
        self.assertEqual(row.education_level, 'BA')
        self.assertEqual(row.min_years_experience, 5)
        self.assertEqual(row.hourly_rate_year1, Decimal('115.99'))
        self.assertEqual(row.current_price, Decimal('115.99'))
        self.assertEqual(row.sin, '132-51')

        row.full_clean()

    def test_price_is_none_when_below_min_rate(self):
        price = FEDERAL_MIN_CONTRACT_RATE - 1.0
        s = s70.Schedule70PriceList(rows=[{
            'sin': '132-51',
            'labor_category': 'Engineer 1',
            'education_level': 'Bachelors',
            'min_years_experience': '2',
            'price_including_iff': str(price),
        }])

        p = self.create_price_list()
        p.save()

        s.add_to_price_list(p)

        row = p.rows.all()[0]

        self.assertEqual(row.current_price, None)

        row.full_clean()

    def test_serialize_and_deserialize_work(self):
        s = s70.Schedule70PriceList.load_from_upload(uploaded_xlsx_file())

        saved = json.dumps(registry.serialize(s))
        restored = registry.deserialize(json.loads(saved))

        self.assertTrue(isinstance(restored, s70.Schedule70PriceList))
        self.assertEqual(s.rows, restored.rows)
