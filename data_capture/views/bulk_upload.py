
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .. import forms
from .utils import add_generic_form_error
from frontend import ajaxform


# TODO: restrict to administrator role
@login_required
def region_10_step_1(request):
    '''Start of Region 10 Bulk Upload - Upload the spreadsheet'''
    if request.method == 'GET':
        form = forms.Region10BulkUploadForm()
    elif request.method == 'POST':
        form = forms.Region10BulkUploadForm(request.POST, request.FILES)

        if form.is_valid():
            request.session['data_capture:bulk_region_10_data'] = \
                form.cleaned_data['gleaned_data']
            return ajaxform.redirect(
                request,
                'data_capture:bulk_region_10_step_2'
            )
        else:
            add_generic_form_error(request, form)

    return ajaxform.render(
        request,
        context={
            'step_number': 1,
            'form': form,
        },
        template_name='data_capture/bulk/region_10.html',
        ajax_template_name='data_capture/bulk/region_10_form.html',
    )


@login_required
def region_10_step_2(request):
    '''Confirm that parsed data is correct and perform the load'''
    data = request.session.get('data_capture:bulk_region_10_data')
    if data is None:
        return redirect('data_capture:bulk_region_10_step_1')

    # TODO: Need to use a Form to have submit and cancel?

    if request.method == 'POST':
        # TODO: Save everything
        del request.session['data_capture:bulk_region_10_data']
        return redirect('data_capture:bulk_region_10_step_3')

    return render(request, 'data_capture/bulk/region_10_step_2.html', {
        'step_number': 2,
        'data': data,
    })


@login_required
def region_10_step_3(request):
    '''Success screen'''
    return render(request, 'data_capture/bulk/region_10_step_3.html', {
        'step_number': 3
    })
