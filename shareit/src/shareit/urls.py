from django.urls import path

from .views import (
    ResourceCreateView,
    ResourceAccessView,
    RESOURCE_ACCESS_VIEW_ARG_UID,
)


urlpatterns = [
    path("", ResourceCreateView.as_view()),
    path(f"<{RESOURCE_ACCESS_VIEW_ARG_UID}>", ResourceAccessView.as_view(), name="access"),
]
