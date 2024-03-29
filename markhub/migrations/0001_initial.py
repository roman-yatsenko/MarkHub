# Generated by Django 3.2.14 on 2022-08-09 14:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivatePublish',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=39, verbose_name='Username')),
                ('repo', models.TextField(max_length=100, verbose_name='Repository name')),
                ('path', models.TextField(max_length=4096, verbose_name='File path')),
                ('published', models.DateTimeField(auto_now_add=True, verbose_name='Publication time')),
                ('content', models.TextField(blank=True, null=True, verbose_name='Rendered content')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User - Repository owner')),
            ],
            options={
                'verbose_name': 'Published file',
                'verbose_name_plural': 'Published files',
                'ordering': ['path'],
                'permissions': (('private_repos', 'Work with private repositories'),),
                'get_latest_by': 'published',
                'unique_together': {('user', 'repo', 'path')},
                'index_together': {('user', 'repo', 'path')},
            },
        ),
    ]
