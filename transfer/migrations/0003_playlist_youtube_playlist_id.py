# Generated by Django 5.2.3 on 2025-06-29 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transfer', '0002_user_spotify_display_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='youtube_playlist_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
