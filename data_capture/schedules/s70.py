import functools
import logging
from django import forms
from django.core.exceptions import ValidationError
import xlrd

from .base import BasePriceList
from contracts.models import EDUCATION_CHOICES
from contracts.management.commands.load_data import FEDERAL_MIN_CONTRACT_RATE


logger = logging.getLogger(__name__)

BAD_ROW_THRESHOLD = 1


def safe_cell_str_value(sheet, rownum, colnum, coercer=None):
    val = ''

    try:
        val = sheet.cell_value(rownum, colnum)
    except IndexError:
        pass

    if coercer is not None:
        try:
            val = coercer(val)
        except ValueError:
            pass

    return str(val)


def is_likely_row(sheet, rownum, rowlen=13):
    # check that the given row's cells are not empty
    for col in range(0, rowlen):
        if not safe_cell_str_value(sheet, rownum, col).strip():
            return False
    return True


def glean_labor_categories_from_file(f, sheet_name='(3)Labor Categories'):
    # TODO: I'm not sure how big these uploaded files can get. While
    # the labor categories price lists don't get that long, according to
    # user research interviews, *product* price lists can get really long;
    # and even though we're not interested in them, information about them
    # is embedded in the workbook, so the file could potentially get large.
    #
    # Unfortunately, it doesn't *seem* like xlrd supports file streaming.
    # Although it does support using memory-mapped files, so perhaps that's a
    # possibility.

    book = xlrd.open_workbook(file_contents=f.read())

    if sheet_name not in book.sheet_names():
        raise ValidationError(
            'There is no sheet in the workbook called "%s".' % sheet_name
        )

    sheet = book.sheet_by_name(sheet_name)

    rownum = 3
    cats = []
    bad_row_count = 0

    while True:
        cval = functools.partial(safe_cell_str_value, sheet, rownum)

        if not is_likely_row(sheet, rownum):
            bad_row_count += 1
            if bad_row_count == BAD_ROW_THRESHOLD:
                # If we've hit the threshold of continuous bad rows, then quit
                break
            else:
                # Else continue and try the next row
                continue
        else:
            # Reset the count of continuous bad rows
            bad_row_count = 0

        cat = {}
        cat['sin'] = cval(0)
        cat['labor_category'] = cval(1)
        cat['education_level'] = cval(2)
        cat['min_years_experience'] = cval(3, coercer=int)
        cat['commercial_list_price'] = cval(4)
        cat['unit_of_issue'] = cval(5)
        cat['most_favored_customer'] = cval(6)
        cat['best_discount'] = cval(7)
        cat['mfc_price'] = cval(8)
        cat['gsa_discount'] = cval(9)
        cat['price_excluding_iff'] = cval(10)
        cat['price_including_iff'] = cval(11)
        cat['volume_discount'] = cval(12)
        cats.append(cat)

        rownum += 1

    return cats


class Schedule70Row(forms.Form):
    sin = forms.CharField(label="SIN(s) proposed")
    labor_category = forms.CharField(
        label="Service proposed (e.g. job title/task)"
    )
    education_level = forms.CharField(
        label="Minimum education / certification level",
    )
    min_years_experience = forms.IntegerField(
        label="Minimum years of experience"
    )
    price_including_iff = forms.DecimalField(
        label="Price offered to GSA (including IFF)"
    )

    def clean_education_level(self):
        value = self.cleaned_data['education_level']

        values = [choice[1] for choice in EDUCATION_CHOICES]

        if value not in values:
            raise ValidationError('This field must contain one of the '
                                  'following values: %s' % (', '.join(values)))

        return value

    def contract_model_education_level(self):
        # Note that due to the way we've cleaned education_level, this
        # code is guaranteed to work.

        return [
            code for code, name in EDUCATION_CHOICES
            if name == self.cleaned_data['education_level']
        ][0]

    def contract_model_hourly_rate_year1(self):
        return self.cleaned_data['price_including_iff']

    def contract_model_current_price(self):
        price = self.contract_model_hourly_rate_year1()
        return price if price >= FEDERAL_MIN_CONTRACT_RATE else None


class Schedule70PriceList(BasePriceList):
    title = 'IT Schedule 70'

    def __init__(self, rows):
        super().__init__()

        self.rows = rows

        for row in self.rows:
            form = Schedule70Row(row)
            if form.is_valid():
                self.valid_rows.append(form)
            else:
                self.invalid_rows.append(form)

    def add_to_price_list(self, price_list):
        for row in self.valid_rows:
            price_list.add_row(
                labor_category=row.cleaned_data['labor_category'],
                education_level=row.contract_model_education_level(),
                min_years_experience=row.cleaned_data['min_years_experience'],
                hourly_rate_year1=row.contract_model_hourly_rate_year1(),
                current_price=row.contract_model_current_price(),
                sin=row.cleaned_data['sin']
            )

    def serialize(self):
        return self.rows

    @classmethod
    def deserialize(cls, rows):
        return cls(rows)

    @classmethod
    def load_from_upload(cls, f):
        try:
            rows = glean_labor_categories_from_file(f)
            return Schedule70PriceList(rows)
        except ValidationError:
            raise
        except Exception as e:
            logger.info('Failed to glean data from %s: %s' % (f.name, e))

            raise ValidationError(
                "An error occurred when reading your Excel data."
            )
