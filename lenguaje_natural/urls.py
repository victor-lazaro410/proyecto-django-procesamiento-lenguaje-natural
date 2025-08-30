from django.urls import path
from . import views
app_name = "lenguaje_natural"
urlpatterns = [
    path("", views.index, name="index"),
    path("upload/", views.upload, name="upload"),
    path("cargar/", views.upload, name="cargar"),
    path("histograma/", views.histograma, name="histograma"),
]
