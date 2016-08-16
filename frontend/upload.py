from django import forms


class UploadWidget(forms.widgets.FileInput):
    '''
    This widget represents an upload widget that the user can
    easily drag-and-drop files into.

    It is tightly coupled to upload.js.
    '''

    def __init__(self, attrs=None, degraded=False,
                 accept=(".xlsx", ".xls", ".csv"),
                 extra_instructions='XLS, XLSX, or CSV format, please.'):
        super().__init__(attrs=attrs)
        self.degraded = degraded
        self.accept = accept
        self.extra_instructions = extra_instructions

    def render(self, name, value, attrs=None):
        degraded_str = ' data-force-degradation' if self.degraded else ''
        final_attrs = {}
        if attrs:
            final_attrs.update(attrs)
        final_attrs['accept'] = ",".join(self.accept)

        id_for_label = final_attrs.get('id', '')

        return "\n".join([
            '<div class="upload"%s>' % degraded_str,
            '  %s' % super().render(name, value, final_attrs),
            '  <div class="upload-chooser">',
            '    <label for="%s">Choose file</label>' % id_for_label,
            '    <span class="js-only" aria-hidden="true">',
            '      or drag and drop here.',
            '    </span>',
            '    <span>%s</span>' % self.extra_instructions,
            '  </div>',
            '</div>'
        ])
