# Generated by Django 5.1.6 on 2025-03-06 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Vaga',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=100)),
                ('descricao', models.TextField()),
                ('localizacao', models.CharField(max_length=100)),
                ('data_postagem', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
