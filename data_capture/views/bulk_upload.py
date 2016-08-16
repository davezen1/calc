

from django.contrib.auth.decorators import login_required

from .. import forms
from .utils import add_generic_form_error
from frontend import ajaxform


# TODO: restrict to administrator role
@login_required
def region_10_step_1(request):
    if request.method == 'GET':
        form = forms.BulkRegion10Form()
    elif request.method == 'POST':
        form = forms.BulkRegion10Form(request.POST, request.FILES)

        if form.is_valid():
            # TODO: set into session
            # request.session['data_capture:bulk_region_10'] = \
            #     form.cleaned_data['gleaned_data']
            return ajaxform.redirect(request, 'bulk_region_10:step_2')
        else:
            add_generic_form_error(request, form)

    return ajaxform.render(
        request,
        context={
            # 'step_number': 1,
            'form': form,
        },
        template_name='data_capture/bulk/region_10.html',
        ajax_template_name='data_capture/bulk/region_10_form.html',
    )
