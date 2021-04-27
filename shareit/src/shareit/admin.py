from typing import Final

from django.contrib import admin
from django.forms import ModelForm, CharField, PasswordInput

from .models import Resource, encode_secret

RESOURCE_SECRET_FIELD_NAME: Final[str] = "secret"


class ResourceForm(ModelForm):

    secret = CharField(widget=PasswordInput())

    class Meta:
        model = Resource
        fields = [RESOURCE_SECRET_FIELD_NAME]


@admin.register(Resource)
class PersonAdmin(admin.ModelAdmin):

    form = ResourceForm
    readonly_fields = ["uri", "url", "expiration_date"]

    @admin.display(description="Uri")
    def uri(self, obj):
        return Resource.encode_uid(obj.uid)

    def save_model(self, request, obj, form, change):
        secret = form.cleaned_data[RESOURCE_SECRET_FIELD_NAME]
        secret_hash = encode_secret(secret)
        obj.secret_hash = secret_hash

        super().save_model(request, obj, form, change)
