import xlrd
import functools
from django import forms

from frontend.upload import UploadWidget
from ..utils import safe_cell_str_value


# 0 text:'Labor Category',
# 1 text:'Year 1/base',
# 2 text:'Year 2',
# 3 text:'Year 3',
# 4 text:'Year 4',
# 5 text:'Year 5',
# 6 text:'Education',
# 7 text:'MinExpAct',
# 8 text:'Bus Size',
# 9 text:'Location',
# 10 text:'COMPANY NAME',
# 11 text:'CONTRACT .',
# 12 text:'Schedule',
# 13 text:'SIN NUMBER',
# 14 text:'Begin Date',
# 15 text:'End Date',
# 16 text:'CurrentYearPricing',
# 17 text:'Contract Year'

# TODO: add coercions
heading_to_contract_field_map = {
    'Labor Category': 'labor_category',
    'Year 1/base': 'hourly_rate_year1',     # normalize_rate
    'Year 2': 'hourly_rate_year2',          # normalize_rate
    'Year 3': 'hourly_rate_year3',          # normalize_rate
    'Year 4': 'hourly_rate_year4',          # normalize_rate
    'Year 5': 'hourly_rate_year5',          # normalize_rate
    'Education': 'education_level',         # convert to education_code
    'MinExpAct': 'min_years_experience',    # convert to int
    'Bus Size': 'business_size',
    'Location': 'contractor_site',
    'COMPANY NAME': 'vendor_name',
    'CONTRACT .': 'idv_piid',
    'Schedule': 'schedule',
    'SIN NUMBER': 'sin',
    'Begin Date': 'contract_start',         # convert to date
    'End Date': 'contract_end',             # convert to date
    'CurrentYearPricing': 'current_price',  # derive this or grab from file?
    'Contract Year': 'contract_year'
}


def get_field_indices_map(sheet, raises=True):
    '''
    Given a sheet, returns a mapping of Contract model field names
    to the column indicies associated with those fields
    '''
    headings = sheet.row(0)

    idx_map = {}
    for i, cell in enumerate(headings):
        # find the val in the heading_to_contract_field_map
        if cell.value in heading_to_contract_field_map:
            idx_map[heading_to_contract_field_map[cell.value]] = i

    if raises and len(idx_map) != len(heading_to_contract_field_map):
        raise Exception  # TODO: proper exception

    return idx_map


def parse_file(file):
    book = xlrd.open_workbook(file_contents=file.read())
    sheet = book.sheet_by_index(0)

    # We use the first row headings instead of depending on order.
    # The headings are pretty weird looking sometimes, ex "CONTRACT ."
    # heading for Contract.idv_piid (Contract Number)
    idx_map = get_field_indices_map(sheet)

    bad_rows = []
    good_rows = []

    # skip the heading row, process the rest
    for i in range(1, sheet.nrows):
        cval = functools.partial(safe_cell_str_value, sheet, i)
        r = {}
        for field, col_num in idx_map.items():
            r[field] = cval(col_num)  # TODO: apply coercions

        # TODO: figure out if a row is good or bad (or maybe this takes
        # place after this step and results shown in final view)
        good_rows.append(r)

    # Need to return both error_rows and good contracts
    return {'contracts': good_rows, 'bad_rows': bad_rows}


class Region10BulkUploadForm(forms.Form):
    '''
    Form for bulk upload of Region 10 data export
    '''
    file = forms.FileField(widget=UploadWidget(
        accept=('.xlsx',),
        extra_instructions="XLSX only, please."
    ))

    def clean(self):
        cleaned_data = super().clean()

        file = cleaned_data.get('file')
        if file:
            # parse the data
            results = parse_file(file)

            if not (results['bad_rows'] or results['contracts']):
                raise forms.ValidationError(
                    "The file you uploaded does not have any data we can "
                    "read from it."
                )

            cleaned_data['results'] = results

        return cleaned_data
