from django import forms
from django.shortcuts import render

from frontend.date import SplitDateField


class ExampleForm(forms.Form):
    date = SplitDateField()


def create_template_context(form=None, is_valid=False):
    return {
        'date_form': form or ExampleForm(),
        'date_form_is_valid': is_valid
    }


def view(request):
    form = None
    is_valid = False

    if request.method == 'POST':
        form = ExampleForm(request.POST)

        if form.is_valid():
            is_valid = True

    ctx = create_template_context(form, is_valid)

    return render(request, 'styleguide_date.html', ctx)
