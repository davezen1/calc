from django.core.management.base import BaseCommand
from django.conf import settings

import csv
import os
import logging

from contracts.models import Contract
from contracts.loaders.region_10 import load_from_something


class Command(BaseCommand):

    def handle(self, *args, **options):
        log = logging.getLogger(__name__)

        log.info("Begin load_data task")

        log.info("Deleting existing contract records")
        Contract.objects.all().delete()

        data_file = csv.reader(
            open(os.path.join(settings.BASE_DIR,
                              'contracts/docs/hourly_prices.csv'), 'r'))

        load_from_something(data_file)
