from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [path("api/", include("trips.urls"))]
frontend = TemplateView.as_view(template_name="index.html")
urlpatterns += [
    path("", frontend, name="frontend"),
    path("plan", frontend),
    path("route", frontend),
    path("logs", frontend),
]
