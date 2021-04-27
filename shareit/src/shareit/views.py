import random
import string
import datetime

from http import HTTPStatus
from typing import Any, TypedDict, Optional, Final

from django.http import Http404, HttpRequest, HttpResponse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import CreateView, FormView
from django.forms import Form, ModelForm, CharField, ValidationError

from .models import Resource, URL_MAXIMUM_LENGTH

RESOURCE_ACCESS_VIEW_ARG_UID: Final[str] = "uid"

RESOURCE_URL_FIELD: Final[str] = "url"
RESOURCE_SECRET_FIELD: Final[str] = "secret"

RESOURCE_SECRET_LENGTH: Final[int] = 12
RESOURCE_SECRET_CHARACTERS: Final[str] = "".join([string.ascii_letters, string.digits])

RESOURCE_INVALID_UUID_ERROR: Final[str] = "Invalid resource UUID"
RESOURCE_INVALID_SECRET_ERROR: Final[str] = "Invalid secret for resource"
RESOURCE_DOES_NOT_EXIST_OR_EXPIRED_ERROR: Final[str] = "Resource does not exist or expired"

TEMPLATE_RESOURCE_CREATE: Final[str] = "resource_create.html"
TEMPLATE_RESOURCE_CREATED: Final[str] = "resource_created.html"
TEMPLATE_RESOURCE_ACCESS: Final[str] = "resource_access.html"
TEMPLATE_RESOURCE_DETAIL: Final[str] = "resource_detail.html"


def generate_secret() -> str:
    """
    Generates random secret.
    """

    secret = [random.choice(RESOURCE_SECRET_CHARACTERS) for _ in range(RESOURCE_SECRET_LENGTH)]

    return "".join(secret)


def get_valid_resource(
    uid: str,
    *,
    now: Optional[datetime.datetime] = None,
) -> Optional[Resource]:
    """
    Gets valid unexpired resource.

    If `now` is not provided, uses current date.

    :param uid: resource encoded UUID
    :param now: date used for expiration date check
    """

    now = now or timezone.now()
    uuid_object = Resource.decode_uid(uid)

    if uuid_object is None:
        return None

    queryset = Resource.objects.filter(uid=uuid_object, expiration_date__gt=now)

    try:
        resource = queryset.get()
    except Resource.DoesNotExist:
        return None

    return resource


class ResourceCreateOut(TypedDict):

    uri: str
    href: str
    secret: str
    expiration_date: datetime.datetime


class ResourceAccessOut(TypedDict):

    url: str
    accessed: int
    expiration_date: datetime.datetime


class ResourceCreateForm(ModelForm):

    url = CharField(required=True, max_length=URL_MAXIMUM_LENGTH)

    class Meta:
        model = Resource
        fields = [RESOURCE_URL_FIELD]


class ResourceAccessForm(Form):

    secret = CharField(required=True, max_length=RESOURCE_SECRET_LENGTH)


class ResourceCreateView(CreateView):

    model = Resource
    form_class = ResourceCreateForm
    template_name = TEMPLATE_RESOURCE_CREATE

    def post(self, request, *args, **kwargs):
        url = request.POST[RESOURCE_URL_FIELD]
        secret = generate_secret()

        resource = Resource.create(url=url, secret=secret)
        resource.save()

        data = ResourceCreateOut(
            uri=resource.uri,
            href=resource.get_absolute_url(),
            secret=secret,
            expiration_date=resource.expiration_date,
        )

        return render(request, TEMPLATE_RESOURCE_CREATED, data)


class ResourceAccessView(FormView):

    form_class = ResourceAccessForm
    template_name = TEMPLATE_RESOURCE_ACCESS

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        now = timezone.now()
        uid = self.kwargs.get(RESOURCE_ACCESS_VIEW_ARG_UID)

        if uid is None:
            return HttpResponse(HTTPStatus.INTERNAL_SERVER_ERROR)

        resource = get_valid_resource(uid, now=now)

        if resource is None:
            raise Http404(RESOURCE_DOES_NOT_EXIST_OR_EXPIRED_ERROR)

        data = self.get_context_data()

        return render(request, TEMPLATE_RESOURCE_ACCESS, data)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        now = timezone.now()
        form = self.get_form()

        if not form.is_valid():
            return self.form_invalid(form)

        uid = self.kwargs.get(RESOURCE_ACCESS_VIEW_ARG_UID)

        if uid is None:
            return HttpResponse(HTTPStatus.INTERNAL_SERVER_ERROR)

        resource = get_valid_resource(uid, now=now)

        if resource is None:
            raise Http404(RESOURCE_DOES_NOT_EXIST_OR_EXPIRED_ERROR)

        secret = form.cleaned_data[RESOURCE_SECRET_FIELD]

        if not resource.verify_secret(secret):
            field = RESOURCE_SECRET_FIELD
            error = ValidationError(RESOURCE_INVALID_SECRET_ERROR)

            form.add_error(field, error)

            return self.form_invalid(form)

        resource.accessed += 1
        resource.save()

        data = ResourceAccessOut(
            url=resource.url,
            accessed=resource.accessed,
            expiration_date=resource.expiration_date,
        )

        return render(request, TEMPLATE_RESOURCE_DETAIL, data)
