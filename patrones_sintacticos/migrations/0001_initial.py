from django.db import migrations, models
import patrones_sintacticos.models

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DocumentoPatrones',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo', models.FileField(upload_to=patrones_sintacticos.models.pat_upload_path)),
                ('nombre_original', models.CharField(blank=True, max_length=255)),
                ('archivo_transformado', models.FileField(blank=True, null=True, upload_to=patrones_sintacticos.models.pat_output_path)),
                ('reservadas', models.IntegerField(default=0)),
                ('variables', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
