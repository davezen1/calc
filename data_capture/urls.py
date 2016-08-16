from django.conf.urls import patterns, url

from .views import price_list_upload, bulk_upload

# TODO: Split into 'bulk' and 'price_list_upload' or something like that

urlpatterns = patterns(
    '',
    url(r'^step/1$', price_list_upload.step_1, name='step_1'),
    url(r'^step/2$', price_list_upload.step_2, name='step_2'),
    url(r'^step/3$', price_list_upload.step_3, name='step_3'),
    url(r'^step/4$', price_list_upload.step_4, name='step_4'),
    url(r'^bulk-region-10$',
        bulk_upload.region_10_step_1, name="bulk_region_10"),
)
