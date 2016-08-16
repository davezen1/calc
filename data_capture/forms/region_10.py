from django import forms
# import xlrd

from frontend.upload import UploadWidget


def file_to_contracts(file):
    return [{'foo': 'bar'}]


class BulkRegion10Form(forms.Form):
    '''
    Form for bulk upload of Region 10 data export
    '''
    file = forms.FileField(widget=UploadWidget(
        accept=('.xlsx',),
        extra_instructions="XLSX only, please."
    ))

    def clean(self):
        cleaned_data = super().clean()

        file = cleaned_data.get('file')
        if file:
            # parse the data
            gleaned_data = file_to_contracts(file)

            if gleaned_data.is_empty():
                raise forms.ValidationError(
                    "The file you uploaded does not have any data we can "
                    "read from it."
                )

            cleaned_data['gleaned_data'] = gleaned_data

        return cleaned_data
