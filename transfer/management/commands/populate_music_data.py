"""
Script para poblar la base de datos con plataformas musicales iniciales
"""
from django.core.management.base import BaseCommand
from transfer.models import MusicPlatform, Genre


class Command(BaseCommand):
    help = 'Poblar base de datos con plataformas musicales y géneros iniciales'

    def handle(self, *args, **options):
        self.stdout.write('Creando plataformas musicales...')
        
        # Plataformas musicales
        platforms = [
            {
                'name': 'spotify',
                'display_name': 'Spotify',
                'icon_url': 'https://cdn.cdnlogo.com/logos/s/89/spotify.svg',
                'color': '#1DB954',
                'supports_oauth': True,
                'api_documentation_url': 'https://developer.spotify.com/documentation/web-api/'
            },
            {
                'name': 'youtube_music',
                'display_name': 'YouTube Music',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/6/6a/Youtube_Music_icon.svg',
                'color': '#FF0000',
                'supports_oauth': True,
                'api_documentation_url': 'https://developers.google.com/youtube/v3'
            },
            {
                'name': 'soundcloud',
                'display_name': 'SoundCloud',
                'icon_url': 'https://cdn.cdnlogo.com/logos/s/91/soundcloud.svg',
                'color': '#FF5500',
                'supports_oauth': True,
                'api_documentation_url': 'https://developers.soundcloud.com/docs/api/guide'
            },
            {
                'name': 'apple_music',
                'display_name': 'Apple Music',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/5/5f/Apple_Music_icon.svg',
                'color': '#FA243C',
                'supports_oauth': True,
                'api_documentation_url': 'https://developer.apple.com/documentation/applemusicapi/'
            },
            {
                'name': 'deezer',
                'display_name': 'Deezer',
                'icon_url': 'https://cdn.cdnlogo.com/logos/d/26/deezer.svg',
                'color': '#FEAA2D',
                'supports_oauth': True,
                'api_documentation_url': 'https://developers.deezer.com/api'
            },
            {
                'name': 'tidal',
                'display_name': 'Tidal',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/0/05/Tidal_%28service%29_logo.svg',
                'color': '#000000',
                'supports_oauth': True,
                'api_documentation_url': 'https://developer.tidal.com/'
            },
            {
                'name': 'amazon_music',
                'display_name': 'Amazon Music',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Amazon-music-logo.svg',
                'color': '#1976D2',
                'supports_oauth': True,
                'is_active': False  # No disponible inicialmente
            },
            {
                'name': 'pandora',
                'display_name': 'Pandora',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Pandora_logo.svg',
                'color': '#005483',
                'supports_oauth': True,
                'is_active': False  # No disponible inicialmente
            }
        ]
        
        for platform_data in platforms:
            platform, created = MusicPlatform.objects.get_or_create(
                name=platform_data['name'],
                defaults=platform_data
            )
            if created:
                self.stdout.write(f'✅ Creada plataforma: {platform.display_name}')
            else:
                self.stdout.write(f'⚪ Ya existe: {platform.display_name}')
        
        self.stdout.write('\nCreando géneros musicales...')
        
        # Géneros musicales principales
        genres = [
            {'name': 'Pop', 'color': '#FF6B6B'},
            {'name': 'Rock', 'color': '#4ECDC4'},
            {'name': 'Hip-Hop', 'color': '#45B7D1'},
            {'name': 'R&B', 'color': '#F9CA24'},
            {'name': 'Electronic', 'color': '#6C5CE7'},
            {'name': 'Country', 'color': '#A0522D'},
            {'name': 'Jazz', 'color': '#2D3436'},
            {'name': 'Classical', 'color': '#74B9FF'},
            {'name': 'Reggae', 'color': '#00B894'},
            {'name': 'Blues', 'color': '#0984E3'},
            {'name': 'Folk', 'color': '#E17055'},
            {'name': 'Indie', 'color': '#FDCB6E'},
            {'name': 'Alternative', 'color': '#E84393'},
            {'name': 'Punk', 'color': '#636E72'},
            {'name': 'Metal', 'color': '#2D3436'},
            {'name': 'Funk', 'color': '#FD79A8'},
            {'name': 'Reggaeton', 'color': '#FF7675'},
            {'name': 'Latin', 'color': '#FDCB6E'},
            {'name': 'World Music', 'color': '#00CEC9'},
            {'name': 'Ambient', 'color': '#81ECEC'},
        ]
        
        for genre_data in genres:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults=genre_data
            )
            if created:
                self.stdout.write(f'✅ Creado género: {genre.name}')
            else:
                self.stdout.write(f'⚪ Ya existe: {genre.name}')
        
        self.stdout.write(self.style.SUCCESS('\n🎵 ¡Base de datos poblada exitosamente!'))
        self.stdout.write(f'Plataformas activas: {MusicPlatform.objects.filter(is_active=True).count()}')
        self.stdout.write(f'Géneros disponibles: {Genre.objects.count()}')
