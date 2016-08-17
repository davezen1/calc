from django.contrib import admin
from django.db import models
from django import forms
from django.utils.safestring import mark_safe

from .schedules import registry
from .models.price_list import SubmittedPriceList, SubmittedPriceListRow


class SubmittedPriceListRowInline(admin.TabularInline):
    model = SubmittedPriceListRow

    can_delete = False

    exclude = ('contract_model',)

    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput}
    }

    def has_add_permission(self, request):
        return False


@admin.register(SubmittedPriceList)
class SubmittedPriceListAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'vendor_name', 'submitter',
                    'is_approved')

    exclude = ('serialized_gleaned_data', 'schedule')

    readonly_fields = ('schedule_title', 'current_status')

    inlines = [
        SubmittedPriceListRowInline
    ]

    def current_status(self, instance):
        if instance.is_approved:
            return mark_safe(
                "<span style=\"color: green\">"
                "This price list has been approved, so its data is now "
                "in CALC. Uncheck the <strong>Is approved</strong> box to "
                "remove its data from CALC.</span>"
            )
        return mark_safe(
            "<span style=\"color: red\">"
            "This price list is not currently approved, so its data is "
            "not in CALC. Check the <strong>Is approved</strong> box to "
            "add its data to CALC."
        )

    def schedule_title(self, instance):
        return registry.get_class(instance.schedule).title

    schedule_title.short_description = 'Schedule'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        original = SubmittedPriceList.objects.get(pk=obj.id)
        if original.is_approved != obj.is_approved:
            if obj.is_approved:
                obj.approve()
            else:
                obj.unapprove()
        obj.save()
