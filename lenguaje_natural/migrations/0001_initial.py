from django.db import migrations, models
import lenguaje_natural.models

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DocumentoLN',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo', models.FileField(upload_to=lenguaje_natural.models.ln_upload_path)),
                ('nombre_original', models.CharField(blank=True, max_length=255)),
                ('tokens_preview', models.TextField(blank=True)),
                ('top_json', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
