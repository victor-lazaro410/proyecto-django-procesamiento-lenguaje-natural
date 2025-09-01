from django.contrib import admin
from .models import DocumentoPatrones
@admin.register(DocumentoPatrones)
class DocumentoPatronesAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_original", "reservadas", "variables", "created_at")
    search_fields = ("nombre_original", "archivo")
    readonly_fields = ("created_at",)
