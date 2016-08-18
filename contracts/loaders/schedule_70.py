import csv
import logging

from django.core.management import call_command
from django.core.exceptions import ValidationError
from datetime import date
from django.db import transaction

from contracts.loaders.region_10 import FEDERAL_MIN_CONTRACT_RATE
from contracts.models import Contract

logger = logging.getLogger(__name__)


class Schedule70Loader(object):
    model = Contract
    schedule_name = 'IT Schedule 70'
    header_rows = 2

    def load(self, filename, replace=True, strict=False):
        logger.info('begin load_s70 task')

        logger.info('reading data')
        contracts = list(self.parse_file(filename, strict=strict))

        logger.info('inserting data')
        self.insert(contracts, replace=replace)

        logger.info('end load_s70 task')

    def parse_file(self, filename, strict=False):
        with open(filename, 'rU') as f:
            reader = csv.reader(f)

            for _ in range(self.header_rows):
                next(reader)

            count = skipped = 0
            for row in reader:
                try:
                    yield self.make_contract(row)
                    count += 1
                except (ValueError, ValidationError) as e:
                    if strict:
                        logger.error('error parsing {}'.format(row))
                        raise
                    else:
                        skipped += 1

            logger.info('rows fetched: {}'.format(count))
            logger.info('rows skipped: {}'.format(skipped))

    @classmethod
    def make_contract(cls, row):
        schedule = row[9]
        if schedule != cls.schedule_name:
            raise ValueError('skipping schedule: {}'.format(schedule))

        price = row[5]
        if not price:
            raise ValueError('missing price')

        price = cls.model.normalize_rate(price)
        display_price = price if price >= FEDERAL_MIN_CONTRACT_RATE else None

        contract = cls.model(
            idv_piid=row[6],
            contract_start=cls.parse_date(row[12]),
            contract_end=cls.parse_date(row[13]),
            contract_year=cls.int_or_fallback(row[11], 1),
            vendor_name=row[7],
            labor_category=row[1].strip().replace('\n', ' '),
            education_level=cls.model.get_education_code(row[2]),
            min_years_experience=cls.int_or_fallback(row[3]),
            hourly_rate_year1=price,
            hourly_rate_year2=None,
            hourly_rate_year3=None,
            hourly_rate_year4=None,
            hourly_rate_year5=None,
            current_price=display_price,
            next_year_price=None,
            second_year_price=None,
            contractor_site=row[10],
            schedule=schedule,
            business_size=row[8],
            sin=row[0]
        )

        contract.full_clean(exclude=['piid'])

        return contract

    @staticmethod
    def int_or_fallback(x, fallback=0):
        try:
            return int(x)
        except ValueError:
            return fallback

    @staticmethod
    def parse_date(s):
        if not s:
            return None

        month, day, year = list(map(int, s.split('/')))
        return date(year, month, day)

    @classmethod
    def insert(cls, contracts, replace=True, update_search_field=True):
        with transaction.atomic():
            if replace:
                logger.info('erasing existing contracts')
                cls.model.objects.filter(schedule=cls.schedule_name).delete()

            logger.info('inserting new contracts')
            cls.model.objects.bulk_create(contracts)

        if update_search_field:
            logger.info('updating search field')
            call_command(
                'update_search_field',
                cls.model._meta.app_label,
                cls.model._meta.model_name
            )
