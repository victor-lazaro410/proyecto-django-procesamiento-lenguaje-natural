from django.urls import path
from . import views

app_name = "ngram"

urlpatterns = [
    path("mle/", views.ngrams_mle_view, name="ngrams_mle"),
    path("", views.ngrams_view, name="ngrams"),
    path("api/", views.ngrams_api, name="ngrams_api"),
    path("autocomplete/", views.autocomplete_view, name="autocomplete"),
]