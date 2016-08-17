from django.db import models
from django.contrib.auth.models import User


# TODO: Parse input XLSX, create Contract models,
# create BulkUploadContractSource and link
# Create and Download XLSX of error rows (dynamically when link clicked)
# Create and Download XLSX of non-error rows (dynamically when link clicked)
class BulkUploadContractSource(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitter = models.ForeignKey(User)
    original_file = models.BinaryField()  # TODO: Not sure if this is necessary
    procurement_center = models.TextField()  # ie "Region 10"
