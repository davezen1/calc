from django.http import HttpResponse
from django.db.models import Avg, Max, Min, Count, Q, StdDev
from decimal import Decimal

from rest_framework.response import Response
from rest_framework.views import APIView

from api.pagination import ContractPagination
from api.serializers import ContractSerializer
from api.utils import get_histogram
from contracts.models import Contract, EDUCATION_CHOICES

import csv


def get_contracts_queryset(request_params, wage_field):
    """ Filters and returns contracts based on query params

    Args:
        request_params (dict): the request query parameters
        wage_field (str): the name of the field currently being used for
            wage calculations and sorting

    Query Params:
        q (str): keywords to search by
        experience_range(str): filter by a range of years of experience
        min_experience (int): filter by minimum years of experience
        max_experience (int): filter by maximum years of experience
        min_education (str): filter by a minimum level of education
            (see EDUCATION_CHOICES)
        schedule (str): filter by GSA schedule
        site (str): filter by worksite
        business_size (str): filter by 's'(mall) or 'o'(ther)
        price (int): filter by exact price
        price__gte (int): price must be greater than or equal to this integer
        price__lte (int): price must be less than or equal to this integer
        sort (str): the column to sort on, defaults to wage_field
        query_type (str): defines how the user's keyword search should work.
            [ match_all (default) | match_phrase | match_exact ]
        exclude: (int): comma separated list of ids to exclude from the search
            results

    Returns:
        QuerySet: a filtered and sorted QuerySet to retrieve Contract objects
    """

    query = request_params.get('q', None)
    experience_range = request_params.get('experience_range', None)
    min_experience = request_params.get('min_experience', None)
    max_experience = request_params.get('max_experience', None)
    min_education = request_params.get('min_education', None)
    education = request_params.get('education', None)
    schedule = request_params.get('schedule', None)
    site = request_params.get('site', None)
    business_size = request_params.get('business_size', None)
    price = request_params.get('price', None)
    price__gte = request_params.get('price__gte')
    price__lte = request_params.get('price__lte')
    sort = request_params.get('sort', wage_field)
    # query_type can be: [ match_all (default) | match_phrase | match_exact ]
    query_type = request_params.get('query_type', 'match_all')
    exclude = request_params.getlist('exclude')

    contracts = Contract.objects.all()

    if exclude:
        # getlist only works for key=val&key=val2, not for key=val1,val2
        exclude = exclude[0].split(',')
        contracts = contracts.exclude(id__in=exclude)

    # excludes records w/o rates for the selected contract period
    contracts = contracts.exclude(**{wage_field + '__isnull': True})

    if query:
        qs = query.split(',')

        if query_type not in ('match_phrase', 'match_exact'):
            contracts = contracts.multi_phrase_search(qs)
        else:
            q_objs = Q()
            for q in qs:
                if query_type == 'match_phrase':
                    q_objs.add(Q(labor_category__icontains=q), Q.OR)
                elif query_type == 'match_exact':
                    q_objs.add(Q(labor_category__iexact=q.strip()), Q.OR)
            contracts = contracts.filter(q_objs)

    if experience_range:
        years = experience_range.split(',')
        min_experience = int(years[0])
        if len(years) > 1:
            max_experience = int(years[1])

    if min_experience:
        contracts = contracts.filter(min_years_experience__gte=min_experience)

    if max_experience:
        contracts = contracts.filter(min_years_experience__lte=max_experience)

    if min_education:
        for index, pair in enumerate(EDUCATION_CHOICES):
            if min_education == pair[0]:
                contracts = contracts.filter(
                    education_level__in=[
                        ed[0] for ed in EDUCATION_CHOICES[index:]
                    ]
                )

    if education:
        degrees = education.split(',')
        selected_degrees = []
        for index, pair in enumerate(EDUCATION_CHOICES):
            if pair[0] in degrees:
                selected_degrees.append(pair[0])
        contracts = contracts.filter(education_level__in=selected_degrees)

    if schedule:
        contracts = contracts.filter(schedule__iexact=schedule)
    if site:
        contracts = contracts.filter(contractor_site__icontains=site)
    if business_size == 's':
        contracts = contracts.filter(business_size__istartswith='s')
    elif business_size == 'o':
        contracts = contracts.filter(business_size__istartswith='o')
    if price:
        contracts = contracts.filter(**{wage_field + '__exact': price})
    else:
        if price__gte:
            contracts = contracts.filter(**{wage_field + '__gte': price__gte})
        if price__lte:
            contracts = contracts.filter(**{wage_field + '__lte': price__lte})

    return contracts.order_by(*sort.split(','))


def quantize(num, precision=2):
    if num is None:
        return None
    return Decimal(num).quantize(Decimal(10) ** -precision)


class GetRates(APIView):

    def get(self, request):
        bins = request.query_params.get('histogram', None)

        wage_field = self.get_wage_field(
            request.query_params.get('contract-year'))
        contracts_all = self.get_queryset(request.query_params, wage_field)

        stats = contracts_all.aggregate(
            Min(wage_field), Max(wage_field),
            Avg(wage_field), StdDev(wage_field))

        page_stats = {
            'minimum': stats[wage_field + '__min'],
            'maximum': stats[wage_field + '__max'],
            'average': quantize(stats[wage_field + '__avg']),
            'first_standard_deviation': quantize(
                stats[wage_field + '__stddev']
            )
        }

        if bins and bins.isnumeric():
            values = contracts_all.values_list(wage_field, flat=True)
            page_stats['wage_histogram'] = get_histogram(values, int(bins))

        pagination = ContractPagination(page_stats)
        results = pagination.paginate_queryset(contracts_all, request)
        serializer = ContractSerializer(results, many=True)
        return pagination.get_paginated_response(serializer.data)

    def get_wage_field(self, year):
        wage_fields = ['current_price', 'next_year_price', 'second_year_price']
        if year in ['1', '2']:
            return wage_fields[int(year)]
        else:
            return 'current_price'

    def get_queryset(self, request, wage_field):
        return get_contracts_queryset(request, wage_field)


class GetRatesCSV(APIView):

    def get(self, request, format=None):
        """
        Returns a CSV of matched records and selected search and filter options

        Query Params:
            q (str): keywords to search by
            min_experience (int): filter by minimum years of experience
            min_education (str): filter by a minimum level of education
            site (str): filter by worksite
            business_size (str): filter by 's'(mall) or 'o'(ther)
        """

        wage_field = 'current_price'
        contracts_all = get_contracts_queryset(request.GET, wage_field)

        q = request.query_params.get('q', 'None')
        min_education = request.query_params.get(
            'min_education', 'None Specified')
        min_experience = request.query_params.get(
            'min_experience', 'None Specified')
        site = request.query_params.get('site', 'None Specified')
        business_size = request.query_params.get(
            'business_size', 'None Specified')
        business_size_map = {
            'o': 'other than small',
            's': 'small business'
        }
        business_size_set = business_size_map.get(business_size)
        if business_size_set:
            business_size = business_size_set

        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = ('attachment; '
                                           'filename="pricing_results.csv"')
        writer = csv.writer(response)
        writer.writerow(("Search Query", "Minimum Education Level",
                         "Minimum Years Experience", "Worksite",
                         "Business Size", "", "", "", "", "", "", "", "", ""))
        writer.writerow((q, min_education, min_experience, site,
                         business_size, "", "", "", "", "", "", "", "", ""))
        writer.writerow(("Contract #", "Business Size", "Schedule", "Site",
                         "Begin Date", "End Date", "SIN", "Vendor Name",
                         "Labor Category", "education Level",
                         "Minimum Years Experience",
                         "Current Year Labor Price", "Next Year Labor Price",
                         "Second Year Labor Price"))

        for c in contracts_all:
            writer.writerow((c.idv_piid, c.get_readable_business_size(),
                             c.schedule, c.contractor_site, c.contract_start,
                             c.contract_end, c.sin, c.vendor_name,
                             c.labor_category, c.get_education_level_display(),
                             c.min_years_experience, c.current_price,
                             c.next_year_price, c.second_year_price))

        return response


class GetAutocomplete(APIView):

    def get(self, request, format=None):
        """
        Query Params:
            q (str): the search query
            query_type (str): defines how the search query should work.
                [ match_all (default) | match_phrase ]
        """

        q = request.query_params.get('q', False)
        query_type = request.query_params.get('query_type', 'match_all')

        if q:
            if query_type == 'match_phrase':
                data = Contract.objects.filter(labor_category__icontains=q)
            else:
                data = Contract.objects.multi_phrase_search(q)
            data = data.values('labor_category').annotate(
                count=Count('labor_category')).order_by('-count')
            return Response(data)
        else:
            return Response([])
