from django.apps import AppConfig

class NgramConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ngram"
    verbose_name = "N-gram Analysis"