import logging
import os

from django.core.management import BaseCommand
from optparse import make_option

from contracts.loaders.schedule_70 import Schedule70Loader

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '''
    Load IT Schedule 70 data into database.

    The order of columns in the input dataset is important.
    The expectation, by column, is:
        1:  sin
        2:  labor_category
        3:  education_level
        4:  min_years_experience
        5:  unit of issue (currently ignored)
        6:  current_price & hourly_rate_year1
        7:  idv_piid
        8:  vendor_name
        9:  business_size
        10: schedule
        11: contractor_site
        12: contract_year
        13: contract_start
        14: contract_end
    '''

    default_filename = 'contracts/docs/s70/s70_data.csv'

    option_list = BaseCommand.option_list + (
        make_option(
            '-f', '--filename',
            default=default_filename,
            help='input filename (.csv, default {})'.format(default_filename)
        ),
        make_option(
            '-a', '--append',
            dest='replace',
            action='store_false',
            default=True,
            help='Append data (default is to replace).'
        ),
        make_option(
            '-s', '--strict',
            action='store_true',
            default=False,
            help='Abort if any input data fails validation.'
        ),
    )

    def handle(self, *args, **options):
        filename = options['filename']
        if not filename or not os.path.exists(filename):
            raise ValueError('invalid filename')

        Schedule70Loader().load(
            filename,
            replace=options['replace'],
            strict=options['strict']
        )
