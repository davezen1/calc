from django.conf.urls import patterns, url

from . import views, ajaxform_example


urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^ajaxform$', ajaxform_example.view, name='ajaxform'),
)
