import logging

from datetime import datetime
from django.core.management import call_command

from contracts.models import Contract

FEDERAL_MIN_CONTRACT_RATE = 10.10

log = logging.getLogger(__name__)


def load_from_something(data_file):
    # skip header row
    next(data_file)

    contracts = []

    log.info("Processing new datafile")
    for line in data_file:
        # replace annoying msft carriage return
        for num in range(0, len(line)):
            # also replace version with capital D
            line[num] = line[num].replace(
                "_x000d_", "").replace("_x000D_", "")

        try:
            if line[0]:
                # create contract record, unique to vendor, labor cat
                idv_piid = line[11]
                vendor_name = line[10]
                labor_category = line[0].strip().replace('\n', ' ')

                contract = Contract()
                contract.idv_piid = idv_piid
                contract.labor_category = labor_category
                contract.vendor_name = vendor_name

                contract.education_level = contract.get_education_code(
                    line[6]
                )
                contract.schedule = line[12]
                contract.business_size = line[8]
                contract.contract_year = line[14]
                contract.sin = line[13]

                if line[15] != '':
                    contract.contract_start = datetime.strptime(
                        line[15], '%m/%d/%Y').date()
                if line[16] != '':
                    contract.contract_end = datetime.strptime(
                        line[16], '%m/%d/%Y').date()

                if line[7].strip() != '':
                    contract.min_years_experience = line[7]
                else:
                    contract.min_years_experience = 0

                if line[1] and line[1] != '':
                    contract.hourly_rate_year1 = contract.normalize_rate(
                        line[1]
                    )
                else:
                    # there's no pricing info
                    continue

                for count, rate in enumerate(line[2:6]):
                    if rate and rate.strip() != '':
                        setattr(contract, 'hourly_rate_year' +
                                str(count + 2),
                                contract.normalize_rate(rate))

                if line[14] and line[14] != '':
                    price_fields = {
                        'current_price': getattr(contract,
                                                 'hourly_rate_year' +
                                                 str(line[14]), 0)
                    }
                    current_year = int(line[14])
                    # we have up to five years of rate data
                    if current_year < 5:
                        price_fields['next_year_price'] = getattr(
                            contract, 'hourly_rate_year' +
                            str(current_year + 1), 0
                        )
                        if current_year < 4:
                            price_fields['second_year_price'] = getattr(
                                contract, 'hourly_rate_year' +
                                str(current_year + 2), 0
                            )

                    # don't create display prices for records where the
                    # rate is under the federal minimum contract rate
                    for field in price_fields:
                        price = price_fields.get(field)
                        if price and price >= FEDERAL_MIN_CONTRACT_RATE:
                            setattr(contract, field, price)

                contract.contractor_site = line[9]

                contracts.append(contract)

        except Exception as e:
            log.exception(e)
            log.warning(line)
            break

    log.info("Inserting records")
    Contract.objects.bulk_create(contracts)

    log.info("Updating search index")
    call_command('update_search_field',
                 Contract._meta.app_label, Contract._meta.model_name)

    log.info("End load_data task")
