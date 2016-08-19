import re
from django.db import models
from django.contrib.auth.models import User
from djorm_pgfulltext.models import SearchManager, SearchQuerySet
from djorm_pgfulltext.fields import VectorField

EDUCATION_CHOICES = (
    ('HS', 'High School'),
    ('AA', 'Associates'),
    ('BA', 'Bachelors'),
    ('MA', 'Masters'),
    ('PHD', 'Ph.D.'),
)


def convert_to_tsquery(query):
    """
    Converts multi-word phrases into AND boolean queries for postgresql.

    Examples:

        >>> convert_to_tsquery('interpretation')
        'interpretation:*'

        >>> convert_to_tsquery('interpretation services')
        'interpretation:* & services:*'
    """

    # remove all non-alphanumeric or whitespace chars
    pattern = re.compile('[^a-zA-Z\s]')
    query = pattern.sub('', query)
    query_parts = query.split()
    # remove empty strings and add :* to use prefix matching on each chunk
    query_parts = ["%s:*" % s for s in query_parts if s]
    tsquery = ' & '.join(query_parts)

    return tsquery


def convert_to_tsquery_union(queries):
    '''
    Converts a list of multi-word phrases into OR boolean queries for
    postgresql.

    Examples:

        >>> convert_to_tsquery_union(['foo', 'bar'])
        'foo:* | bar:*'

        >>> convert_to_tsquery_union(['foo', 'bar baz'])
        'foo:* | bar:* & baz:*'

    Also, unrecognizable/garbage phrases will be removed:

        >>> convert_to_tsquery_union(['foo', '$@#%#@!', 'bar'])
        'foo:* | bar:*'
    '''

    queries = [convert_to_tsquery(query) for query in queries]
    # remove empty strings
    queries = filter(None, queries)
    return " | ".join(queries)


class CurrentContractManager(SearchManager):
    # need to subclass the SearchManager we were using for postgres full text
    # search instead of default

    def multi_phrase_search(self, *args, **kwargs):
        return self.get_queryset().multi_phrase_search(*args, **kwargs)

    def get_queryset(self):
        return ContractsQuerySet(self.model, using=self._db)\
            .filter(current_price__gt=0)\
            .exclude(current_price__isnull=True)


class ContractsQuerySet(SearchQuerySet):

    def multi_phrase_search(self, queries):
        if isinstance(queries, str):
            queries = [queries]
        return self.search(convert_to_tsquery_union(queries), raw=True)

    def order_by(self, *args, **kwargs):
        edu_sort_sql = """
            case
                when education_level = 'HS' then 1
                when education_level = 'AA' then 2
                when education_level = 'BA' then 3
                when education_level = 'MA' then 4
                when education_level = 'PHD' then 5
                else -1
            end
        """

        edu_index = None

        sort_params = list(args)

        if 'education_level' in sort_params:
            edu_index = sort_params.index('education_level')
        elif '-education_level' in sort_params:
            edu_index = sort_params.index('-education_level')

        if edu_index is not None:
            sort_params[edu_index] = 'edu_sort' if not args[
                edu_index].startswith('-') else '-edu_sort'
            queryset = super(ContractsQuerySet, self)\
                .extra(select={'edu_sort': edu_sort_sql}, order_by=sort_params)
        else:
            queryset = super(ContractsQuerySet, self)\
                .order_by(*args, **kwargs)

        return queryset


class BulkUploadContractSource(models.Model):
    '''
    Model to store provenance of bulk-uploaded contract data
    '''
    REGION_10 = 'R10'

    PROCUREMENT_CENTER_CHOICES = (
        (REGION_10, 'Region 10'),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitter = models.ForeignKey(User, null=True, blank=True)
    has_been_loaded = models.BooleanField(default=False)
    original_file = models.BinaryField()
    procurement_center = models.CharField(
        db_index=True, max_length=5, choices=PROCUREMENT_CENTER_CHOICES)


class Contract(models.Model):

    idv_piid = models.CharField(max_length=128)  # index this field
    piid = models.CharField(max_length=128)  # index this field
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)
    contract_year = models.IntegerField(null=True, blank=True)
    vendor_name = models.CharField(max_length=128)
    labor_category = models.TextField(db_index=True)
    education_level = models.CharField(
        db_index=True, choices=EDUCATION_CHOICES, max_length=5, null=True,
        blank=True)
    min_years_experience = models.IntegerField(db_index=True)
    hourly_rate_year1 = models.DecimalField(max_digits=10, decimal_places=2)
    hourly_rate_year2 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    hourly_rate_year3 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    hourly_rate_year4 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    hourly_rate_year5 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    current_price = models.DecimalField(
        db_index=True, max_digits=10, decimal_places=2, null=True, blank=True)
    next_year_price = models.DecimalField(
        db_index=True, max_digits=10, decimal_places=2, null=True, blank=True)
    second_year_price = models.DecimalField(
        db_index=True, max_digits=10, decimal_places=2, null=True, blank=True)
    contractor_site = models.CharField(
        db_index=True, max_length=128, null=True, blank=True)
    schedule = models.CharField(
        db_index=True, max_length=128, null=True, blank=True)
    business_size = models.CharField(
        db_index=True, max_length=128, null=True, blank=True)
    sin = models.TextField(null=True, blank=True)

    search_index = VectorField()

    upload_source = models.ForeignKey(
        BulkUploadContractSource,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    # use a manager that filters by current contracts with a valid
    # current_price
    objects = CurrentContractManager(
        fields=('labor_category',),
        config='pg_catalog.english',
        search_field='search_index',
        auto_update_search_field=True
    )

    def get_readable_business_size(self):
        if 's' in self.business_size.lower():
            return 'small business'
        else:
            return 'other than small business'

    @staticmethod
    def get_education_code(text):
        for pair in EDUCATION_CHOICES:
            if text.strip() in pair[1]:
                return pair[0]

        return None

    @staticmethod
    def normalize_rate(rate):
        return float(rate.replace(',', '').replace('$', ''))
