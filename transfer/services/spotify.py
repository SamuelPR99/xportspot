import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class SpotifyAuthService:
    """Servicio para manejar la autenticación con Spotify"""
    
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = f"{settings.BACKEND_URL}/api/auth/spotify/callback/"
        
        self.scope = [
            'user-read-private',
            'user-read-email', 
            'playlist-read-private',
            'playlist-read-collaborative',
            'playlist-modify-public',
            'playlist-modify-private'
        ]
    
    def get_auth_url(self):
        """Obtener URL de autorización de Spotify"""
        try:
            sp_oauth = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=' '.join(self.scope),
                show_dialog=True
            )
            
            auth_url = sp_oauth.get_authorize_url()
            return {'auth_url': auth_url}
            
        except Exception as e:
            logger.error(f"Error al generar URL de autorización de Spotify: {e}")
            raise Exception("Error al conectar con Spotify")
    
    def exchange_code_for_tokens(self, code):
        """Intercambiar código de autorización por tokens"""
        try:
            sp_oauth = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=' '.join(self.scope)
            )
            
            token_info = sp_oauth.get_access_token(code)
            return token_info
            
        except Exception as e:
            logger.error(f"Error al intercambiar código por tokens: {e}")
            raise Exception("Error al obtener tokens de Spotify")
    
    def get_user_info(self, access_token):
        """Obtener información del usuario usando un access token"""
        try:
            sp = spotipy.Spotify(auth=access_token)
            user_info = sp.current_user()
            return user_info
            
        except Exception as e:
            logger.error(f"Error al obtener información del usuario: {e}")
            raise Exception("Error al obtener información del usuario de Spotify")

    def handle_callback(self, code, user):
        """Manejar callback de autorización de Spotify"""
        try:
            sp_oauth = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=' '.join(self.scope)
            )
            
            # Intercambiar código por tokens
            token_info = sp_oauth.get_access_token(code)
            
            if not token_info:
                raise Exception("No se pudo obtener token de acceso")
            
            # Crear cliente de Spotify con el token
            sp = spotipy.Spotify(auth=token_info['access_token'])
            
            # Obtener información del usuario de Spotify
            spotify_user = sp.current_user()
            
            # Actualizar información del usuario
            user.spotify_user_id = spotify_user['id']
            user.spotify_display_name = spotify_user.get('display_name') or spotify_user['id']
            user.spotify_access_token = token_info['access_token']
            user.spotify_refresh_token = token_info.get('refresh_token')
            user.spotify_token_expires_at = timezone.now() + timezone.timedelta(
                seconds=token_info.get('expires_in', 3600)
            )
            user.profile_image = spotify_user['images'][0]['url'] if spotify_user['images'] else None
            user.country = spotify_user.get('country')
            user.spotify_premium = spotify_user.get('product') == 'premium'
            user.spotify_connected_at = timezone.now()
            user.save()
            
            return {
                'success': True,
                'user_info': {
                    'spotify_id': spotify_user['id'],
                    'display_name': spotify_user.get('display_name'),
                    'email': spotify_user.get('email'),
                    'country': spotify_user.get('country'),
                    'premium': spotify_user.get('product') == 'premium'
                }
            }
            
        except Exception as e:
            logger.error(f"Error en callback de Spotify: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def refresh_token(self, user):
        """Refrescar token de acceso de Spotify"""
        try:
            if not user.spotify_refresh_token:
                raise Exception("No hay refresh token disponible")
            
            sp_oauth = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=' '.join(self.scope)
            )
            
            token_info = sp_oauth.refresh_access_token(user.spotify_refresh_token)
            
            # Actualizar tokens
            user.spotify_access_token = token_info['access_token']
            if 'refresh_token' in token_info:
                user.spotify_refresh_token = token_info['refresh_token']
            user.spotify_token_expires_at = timezone.now() + timezone.timedelta(
                seconds=token_info.get('expires_in', 3600)
            )
            user.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error al refrescar token de Spotify: {e}")
            return False
    
    def disconnect_user(self, user):
        """Desconectar usuario de Spotify"""
        user.spotify_user_id = None
        user.spotify_display_name = None
        user.spotify_access_token = None
        user.spotify_refresh_token = None
        user.spotify_token_expires_at = None
        user.spotify_connected_at = None
        user.profile_image = None
        user.country = None
        user.spotify_premium = False
        user.save()


class SpotifyPlaylistService:
    """Servicio para manejar playlists de Spotify"""
    
    def __init__(self, user):
        self.user = user
        if not user.has_spotify_connected:
            raise Exception("Usuario no conectado a Spotify")
        
        # Verificar si el token ha expirado y refrescarlo automáticamente
        if (user.spotify_token_expires_at and 
            timezone.now() >= user.spotify_token_expires_at):
            auth_service = SpotifyAuthService()
            success = auth_service.refresh_token(user)
            if not success:
                raise Exception("Token de Spotify expirado y no se pudo refrescar. Por favor, reconecta tu cuenta.")
        
        # Verificar que tenemos un token válido
        if not user.spotify_access_token:
            raise Exception("No hay token de acceso válido. Por favor, reconecta tu cuenta de Spotify.")
        
        self.sp = spotipy.Spotify(auth=user.spotify_access_token)
    
    def get_user_playlists(self):
        """Obtener playlists del usuario"""
        try:
            playlists = []
            results = self.sp.current_user_playlists(limit=50)
            
            while results:
                for playlist in results['items']:
                    playlists.append({
                        'id': playlist['id'],
                        'name': playlist['name'],
                        'description': playlist['description'],
                        'track_count': playlist['tracks']['total'],
                        'public': playlist['public'],
                        'collaborative': playlist['collaborative'],
                        'owner': playlist['owner']['display_name'],
                        'images': playlist['images']
                    })
                
                if results['next']:
                    results = self.sp.next(results)
                else:
                    break
            
            return playlists
            
        except Exception as e:
            logger.error(f"Error al obtener playlists: {e}")
            raise Exception("Error al obtener playlists de Spotify")
    
    def import_playlist(self, spotify_playlist_id, name=None, description=None):
        """Importar una playlist desde Spotify"""
        try:
            # Obtener información de la playlist
            playlist_info = self.sp.playlist(spotify_playlist_id)
            
            # Usar nombre y descripción proporcionados o los de Spotify
            playlist_name = name or playlist_info['name']
            playlist_description = description or playlist_info.get('description', '')
            
            # Verificar si la playlist ya existe para este usuario
            from ..models import Playlist, Song, PlaylistSong
            
            existing_playlist = Playlist.objects.filter(
                user=self.user,
                spotify_id=spotify_playlist_id
            ).first()
            
            if existing_playlist:
                raise Exception("Esta playlist ya ha sido importada")
            
            # Crear la playlist en la base de datos
            playlist = Playlist.objects.create(
                user=self.user,
                spotify_id=spotify_playlist_id,
                name=playlist_name,
                description=playlist_description,
                total_tracks=playlist_info['tracks']['total']
            )
            
            # Obtener las canciones de la playlist
            tracks = self.get_playlist_tracks(spotify_playlist_id)
            
            # Importar las canciones
            for position, track_data in enumerate(tracks):
                # Crear o obtener la canción usando name + artist como clave única
                song, created = Song.objects.get_or_create(
                    name=track_data['name'],
                    artist=', '.join(track_data['artists']),
                    defaults={
                        'album': track_data['album'],
                        'spotify_id': track_data['spotify_id'],
                        'duration_ms': track_data['duration_ms'],
                        'preview_url': track_data.get('preview_url'),
                        'spotify_url': track_data['external_urls'].get('spotify')
                    }
                )
                
                # Si la canción ya existía pero no tenía spotify_id, actualizarlo
                if not created and not song.spotify_id:
                    song.spotify_id = track_data['spotify_id']
                    if not song.spotify_url:
                        song.spotify_url = track_data['external_urls'].get('spotify')
                    song.save()
                
                # Asociar la canción con la playlist
                PlaylistSong.objects.create(
                    playlist=playlist,
                    song=song,
                    position=position + 1
                )
            
            # Actualizar el total de tracks
            playlist.total_tracks = len(tracks)
            playlist.save()
            
            return playlist
            
        except Exception as e:
            logger.error(f"Error al importar playlist: {e}")
            raise Exception(f"Error al importar playlist: {str(e)}")

    def get_playlist_tracks(self, playlist_id):
        """Obtener canciones de una playlist"""
        try:
            tracks = []
            results = self.sp.playlist_tracks(playlist_id)
            
            while results:
                for item in results['items']:
                    if item['track'] and item['track']['type'] == 'track':
                        track = item['track']
                        tracks.append({
                            'spotify_id': track['id'],
                            'name': track['name'],
                            'artists': [artist['name'] for artist in track['artists']],
                            'album': track['album']['name'],
                            'duration_ms': track['duration_ms'],
                            'preview_url': track['preview_url'],
                            'external_urls': track['external_urls']
                        })
                
                if results['next']:
                    results = self.sp.next(results)
                else:
                    break
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error al obtener tracks de playlist: {e}")
            raise Exception("Error al obtener canciones de Spotify")
