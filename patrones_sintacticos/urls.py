from django.urls import path
from . import views
app_name = "patrones_sintacticos"
urlpatterns = [
    path("", views.index, name="index"),
    path("upload/", views.upload_txt, name="upload"),
]
