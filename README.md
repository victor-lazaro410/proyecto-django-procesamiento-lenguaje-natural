# Proyecto PLN Completo (Django)
## Pasos
1) Crea y activa un entorno virtual, instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2) Migraciones:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser  # opcional
   ```
3) Levanta:
   ```bash
   python manage.py runserver
   ```
4) URLs:
   - `/` (mitad y mitad)
   - `/lenguaje/` (subir .txt/.csv → tokens limpios + Top 30)
   - `/patrones/` (subir .txt → descarga transformado)
   - `/admin/` (ver documentos guardados)
> Media se guarda en `media/`. Si tenías `last.txt` anterior, puedes copiarlo a `media/uploads_lenguaje/last.txt` y abrir `/lenguaje/` o ejecutar `python manage.py backfill_lenguaje`.
