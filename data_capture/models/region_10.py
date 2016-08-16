from django.db import models
from django.contrib.auth.models import User

from contracts.models import Contract, EDUCATION_CHOICES

# TODO: Should standardize these choices across models,
# perhaps just make a Boolean is_small_business
BUSINESS_SIZE_CHOICES = (
    ('S', 'Small Business'),
    ('O', 'Other than a Small Business')
)

# TODO: Standardize these across models
CONTRACTOR_SITE_CHOICES = (
    ('Customer', 'Customer'),
    ('Contractor', 'Contractor'),
    ('Both', 'Both'),
)


class SubmittedRegion10Export(models.Model):
    '''Model for Region 10 Bulk Export files'''
    submitter = models.ForeignKey(User)
    serialized_gleaned_data = models.TextField(
        help_text=(
            'The JSON-serialized data from the upload, including '
            'information about any rows that failed validation.'
        )
    )
    pass


class SubmittedRegion10ExportRow(models.Model):
    '''Model for each row in a Region 10 Bulk Export file'''

    # TODO: determine null and blank settings for all fields
    labor_category = models.TextField()
    hourly_rate_year1 = models.DecimalField(max_digits=10, decimal_places=2)
    hourly_rate_year2 = models.DecimalField(max_digits=10, decimal_places=2)
    hourly_rate_year3 = models.DecimalField(max_digits=10, decimal_places=2)
    hourly_rate_year4 = models.DecimalField(max_digits=10, decimal_places=2)
    hourly_rate_year5 = models.DecimalField(max_digits=10, decimal_places=2)
    education_level = models.CharField(
        choices=EDUCATION_CHOICES, max_length=5, null=True,
        blank=True)
    min_years_experience = models.IntegerField()
    business_size = models.CharField(
        choices=BUSINESS_SIZE_CHOICES, max_length=1, null=True, blank=True
    )
    contractor_site = models.CharField(
        verbose_name='Worksite',
        choices=CONTRACTOR_SITE_CHOICES,
        max_length=128,
    )
    vendor_name = models.CharField(max_length=128)
    contract_number = models.CharField(max_length=128)
    schedule = models.CharField(max_length=128)
    sin = models.TextField(null=True, blank=True)
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)
    # current price is derived from the hourly_rate fields and contract_year
    # current_price = models.DecimalField(max_digits=10, decimal_places=2)
    contract_year = models.IntegerField(null=True, blank=True)

    export = models.ForeignKey(
        SubmittedRegion10Export,
        on_delete=models.CASCADE,
        related_name='rows'
    )

    contract_model = models.OneToOneField(
        Contract,
        # TODO: CASCADE instead?
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        # This is really just so price list rows don't appear as
        # 'SubmittedPriceListRow object' in Django admin.
        return 'Submitted region 10 export row'
