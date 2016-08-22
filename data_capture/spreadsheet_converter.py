import xlrd

from xlrd.book import XL_CELL_DATE
from xlrd.xldate import xldate_as_datetime


class Region10SpreadsheetConverter():
    '''
    Used to convert Region 10 database export XLS/X file to a CSV-like
    collection of row objects
    '''

    sheet_index = 0

    def __init__(self, xls_file):
        self.xls_file = xls_file

    # Dict of R10 Excel sheet headings to the expected col index of CSV rows
    # loaded by the existing R10 data loader
    #
    # ref: contracts.loaders.Region10Loader#make_contract
    xl_heading_to_csv_idx_map = {
        'Labor Category': 0,    # 'labor_category'
        'Year 1/base': 1,       # 'hourly_rate_year1'
        'Year 2': 2,            # 'hourly_rate_year2'
        'Year 3': 3,            # 'hourly_rate_year3'
        'Year 4': 4,            # 'hourly_rate_year4'
        'Year 5': 5,            # 'hourly_rate_year5'
        'Education': 6,         # 'education_level'
        'MinExpAct': 7,         # 'min_years_experience'
        'Bus Size': 8,          # 'business_size'
        'Location': 9,          # 'contractor_site'
        'COMPANY NAME': 10,     # 'vendor_name'
        'CONTRACT .': 11,       # 'idv_piid'
        'Schedule': 12,         # 'schedule'
        'SIN NUMBER': 13,       # 'sin'
        'Contract Year': 14,    # 'contract_year'
        'Begin Date': 15,       # 'contract_start'
        'End Date': 16,         # 'contract_end'
        # Unused 'CurrentYearPricing' because it is derived
    }

    def is_valid_file(self):
        '''
        Check that given file is a valid Region 10 data spreadsheet
        '''
        try:
            book = xlrd.open_workbook(file_contents=self.xls_file.read())
            sheet = book.sheet_by_index(self.sheet_index)
            self.get_heading_indices_map(sheet, raises=True)
        except ValueError as e:
            return False

        self.xls_file.seek(0)
        return True

    def get_metadata(self):
        '''
        Returns a dict containing metadata about the related xls_file
        '''
        book = xlrd.open_workbook(file_contents=self.xls_file.read())
        sheet = book.sheet_by_index(self.sheet_index)
        self.xls_file.seek(0)
        return {
            'num_rows': sheet.nrows - 1  # subtract 1 for the header row
        }

    def convert_next(self):
        '''
        Returns a generator that yields converted rows. The conversion is
        from the related xls_file to the CSV row format expected by
        contracts.loaders.region_10.Region10Loader
        '''
        book = xlrd.open_workbook(file_contents=self.xls_file.read())

        datemode = book.datemode  # necessary for Excel date parsing

        sheet = book.sheet_by_index(self.sheet_index)

        heading_indices = self.get_heading_indices_map(sheet)

        # skip the heading row, process the rest
        for rx in range(1, sheet.nrows):
            row = [None] * len(self.xl_heading_to_csv_idx_map)  # init row

            for heading, xl_idx in heading_indices.items():
                # item_val = cval(xl_idx)
                cell = sheet.cell(rx, xl_idx)

                cell_type = cell.ctype
                cell_value = cell.value

                csv_col_idx = self.xl_heading_to_csv_idx_map[heading]

                if cell_type is XL_CELL_DATE:
                    # convert to mm/dd/YYYY string
                    date = xldate_as_datetime(cell_value, datemode)
                    cell_value = date.strftime('%m/%d/%Y')

                # Save the string value into the expected CSV col
                # index of the row
                row[csv_col_idx] = str(cell_value)

            yield row

        self.xls_file.seek(0)
        return

    def convert_file(self):
        '''
        Converts the input Region 10 XLS/X spreadsheet to a list
        of CSV-like rows expected by contracts.loaders.region_10.Region10Loader
        '''
        return list(self.convert_next())

    def get_heading_indices_map(self, sheet, raises=True):
        '''
        Given a sheet, returns a mapping of R10 Excel sheet headings
        to the column indices associated with those fields in that sheet
        '''
        headings = sheet.row(0)

        idx_map = {}
        for i, cell in enumerate(headings):
            # find the val in the xl_heading_to_csv_idx_map
            if cell.value in self.xl_heading_to_csv_idx_map:
                idx_map[cell.value] = i

        if raises and len(idx_map) != len(self.xl_heading_to_csv_idx_map):
            raise ValueError('Missing expected column(s) in Excel sheet')

        return idx_map
