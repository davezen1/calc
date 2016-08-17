from django import forms
from django.shortcuts import render

from frontend.upload import UploadWidget
from . import ajaxform_example


def get_degraded_upload_widget():
    class MyForm(forms.Form):
        file = forms.FileField(widget=UploadWidget(degraded=True))

    return MyForm()['file']


def index(request):
    ctx = {
        'degraded_upload_widget': get_degraded_upload_widget()
    }
    ctx.update(ajaxform_example.create_template_context())

    return render(request, 'styleguide.html', ctx)
