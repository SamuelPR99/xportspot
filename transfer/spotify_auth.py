import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class SpotifyAuthService:
    """Servicio para manejar la autenticación con Spotify"""
    
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = "http://localhost:3000/callback/spotify"
        self.scope = "user-read-private user-read-email playlist-read-private playlist-read-collaborative"
    
    def get_auth_url(self):
        """Obtener URL de autorización de Spotify"""
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            show_dialog=True
        )
        return sp_oauth.get_authorize_url()
    
    def get_token_from_code(self, code):
        """Obtener token de acceso usando el código de autorización"""
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        return sp_oauth.get_access_token(code)
    
    def create_or_update_user(self, token_info):
        """Crear o actualizar usuario con información de Spotify"""
        access_token = token_info['access_token']
        refresh_token = token_info.get('refresh_token')
        expires_at = timezone.now() + timezone.timedelta(seconds=token_info['expires_in'])
        
        # Obtener información del usuario desde Spotify
        sp = spotipy.Spotify(auth=access_token)
        user_info = sp.current_user()
        
        # Buscar usuario existente por spotify_user_id
        try:
            user = User.objects.get(spotify_user_id=user_info['id'])
            # Actualizar tokens
            user.spotify_access_token = access_token
            user.spotify_refresh_token = refresh_token
            user.spotify_token_expires_at = expires_at
            user.last_spotify_sync = timezone.now()
            user.save()
        except User.DoesNotExist:
            # Crear nuevo usuario
            username = user_info.get('display_name', user_info['id'])
            email = user_info.get('email', f"{user_info['id']}@spotify.local")
            
            # Asegurar que el username sea único
            original_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                spotify_user_id=user_info['id'],
                spotify_access_token=access_token,
                spotify_refresh_token=refresh_token,
                spotify_token_expires_at=expires_at,
                profile_image=user_info.get('images', [{}])[0].get('url') if user_info.get('images') else None,
                country=user_info.get('country'),
                spotify_premium=user_info.get('product') == 'premium',
                spotify_connected_at=timezone.now(),
                last_spotify_sync=timezone.now()
            )
        
        return user
    
    def refresh_token(self, user):
        """Renovar el token de acceso de Spotify"""
        if not user.spotify_refresh_token:
            raise Exception("No refresh token available")
        
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        
        token_info = sp_oauth.refresh_access_token(user.spotify_refresh_token)
        
        user.spotify_access_token = token_info['access_token']
        if 'refresh_token' in token_info:
            user.spotify_refresh_token = token_info['refresh_token']
        user.spotify_token_expires_at = timezone.now() + timezone.timedelta(seconds=token_info['expires_in'])
        user.last_spotify_sync = timezone.now()
        user.save()
        
        return user
    
    def get_spotify_client(self, user):
        """Obtener cliente de Spotify para un usuario"""
        # Verificar si el token ha expirado
        if user.spotify_token_expires_at and user.spotify_token_expires_at <= timezone.now():
            user = self.refresh_token(user)
        
        return spotipy.Spotify(auth=user.spotify_access_token)
    
    def get_user_playlists(self, user):
        """Obtener playlists del usuario desde Spotify"""
        sp = self.get_spotify_client(user)
        playlists = []
        
        results = sp.current_user_playlists(limit=50)
        playlists.extend(results['items'])
        
        while results['next']:
            results = sp.next(results)
            playlists.extend(results['items'])
        
        return playlists
    
    def get_playlist_tracks(self, user, playlist_id):
        """Obtener canciones de una playlist desde Spotify"""
        sp = self.get_spotify_client(user)
        tracks = []
        
        results = sp.playlist_tracks(playlist_id, limit=100)
        tracks.extend(results['items'])
        
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
        
        return tracks
