from django.contrib import admin
from django.utils.html import format_html
import json
from .models import DocumentoLN
@admin.register(DocumentoLN)
class DocumentoLNAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_original", "created_at", "top10")
    search_fields = ("nombre_original", "archivo")
    readonly_fields = ("created_at", "tokens_preview", "top_json", "top_html")
    def top10(self, obj):
        try:
            top = json.loads(obj.top_json or "[]")[:10]
        except Exception:
            top = []
        return ", ".join(f"{w}:{c}" for w, c in top) if top else "(sin datos)"
    top10.short_description = "Top10"
    def top_html(self, obj):
        try:
            top = json.loads(obj.top_json or "[]")
        except Exception:
            top = []
        if not top:
            return "(sin datos)"
        rows = "".join(f"<tr><td>{i+1}</td><td>{w}</td><td>{c}</td></tr>" for i,(w,c) in enumerate(top))
        return format_html('<table style="border-collapse:collapse"><thead><tr><th>#</th><th>Palabra</th><th>Frecuencia</th></tr></thead><tbody>{}</tbody></table>', rows)
    top_html.short_description = "Top completo (HTML)"
