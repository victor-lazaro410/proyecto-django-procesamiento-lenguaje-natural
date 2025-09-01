from django.urls import path
from . import views

app_name = "ngram"

urlpatterns = [
    path("", views.ngrams_view, name="ngrams"),
    path("api/", views.ngrams_api, name="ngrams_api"),
]