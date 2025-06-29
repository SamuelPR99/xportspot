"""
Servicio de autenticación OAuth de Google para YouTube Music
"""
import os
import json
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Servicio para manejar autenticación OAuth de Google/YouTube"""
    
    # Scopes necesarios para YouTube Music
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.readonly',
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
    
    def __init__(self):
        self.client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', None)
        self.redirect_uri = getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', 'http://localhost:8000/api/google/callback/')
        
        if not self.client_id or not self.client_secret:
            logger.warning("Google OAuth credentials not configured")
    
    def get_authorization_url(self, state=None):
        """Genera la URL de autorización de Google OAuth"""
        try:
            # Configuración del flow OAuth
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.SCOPES
            )
            flow.redirect_uri = self.redirect_uri
            
            # Generar URL de autorización
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state,
                prompt='consent'  # Fuerza mostrar la pantalla de consentimiento
            )
            
            return authorization_url, state
            
        except Exception as e:
            logger.error(f"Error generating Google authorization URL: {e}")
            return None, None
    
    def exchange_code_for_tokens(self, authorization_code, state=None):
        """Intercambia el código de autorización por tokens de acceso"""
        try:
            # Configurar el flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.SCOPES,
                state=state
            )
            flow.redirect_uri = self.redirect_uri
            
            # Intercambiar código por tokens
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            # Obtener información del usuario
            user_info = self.get_user_info(credentials)
            
            return {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_at': credentials.expiry,
                'user_info': user_info
            }
            
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            return None
    
    def get_user_info(self, credentials):
        """Obtiene información del usuario desde Google"""
        try:
            # Crear servicio de OAuth2 para obtener info del usuario
            oauth2_service = build('oauth2', 'v2', credentials=credentials)
            user_info = oauth2_service.userinfo().get().execute()
            
            return {
                'google_id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'verified_email': user_info.get('verified_email', False)
            }
            
        except HttpError as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def refresh_access_token(self, refresh_token):
        """Refresca el token de acceso usando el refresh token"""
        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Refrescar token
            credentials.refresh(Request())
            
            return {
                'access_token': credentials.token,
                'expires_at': credentials.expiry
            }
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    def revoke_access(self, token):
        """Revoca el acceso del token"""
        try:
            import requests
            revoke_url = f"https://oauth2.googleapis.com/revoke?token={token}"
            response = requests.post(revoke_url)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    def get_youtube_service(self, access_token):
        """Crea un servicio de YouTube API con el token de acceso"""
        try:
            credentials = Credentials(token=access_token)
            youtube_service = build('youtube', 'v3', credentials=credentials)
            return youtube_service
            
        except Exception as e:
            logger.error(f"Error creating YouTube service: {e}")
            return None
    
    def test_connection(self, access_token):
        """Prueba la conexión con YouTube API"""
        try:
            youtube_service = self.get_youtube_service(access_token)
            if not youtube_service:
                return False, "No se pudo crear el servicio de YouTube"
            
            # Probar obtener canales del usuario
            request = youtube_service.channels().list(
                part="snippet,contentDetails,statistics",
                mine=True
            )
            response = request.execute()
            
            channels = response.get('items', [])
            if channels:
                channel = channels[0]
                return True, {
                    'channel_title': channel['snippet']['title'],
                    'channel_id': channel['id'],
                    'subscriber_count': channel.get('statistics', {}).get('subscriberCount', 'N/A'),
                    'video_count': channel.get('statistics', {}).get('videoCount', 'N/A')
                }
            else:
                return False, "No se encontraron canales asociados a esta cuenta"
                
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return False, f"Error de API de YouTube: {e}"
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return False, f"Error de conexión: {e}"


class YouTubeMusicService:
    """Servicio para interactuar con YouTube Music usando OAuth"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.google_service = GoogleOAuthService()
        self.youtube_service = self.google_service.get_youtube_service(access_token)
    
    def create_playlist(self, title, description="", privacy_status="private"):
        """Crea una nueva playlist en YouTube"""
        try:
            if not self.youtube_service:
                return None, "Servicio de YouTube no disponible"
            
            # Crear playlist
            request = self.youtube_service.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                        "defaultLanguage": "es",
                        "localized": {
                            "title": title,
                            "description": description
                        }
                    },
                    "status": {
                        "privacyStatus": privacy_status
                    }
                }
            )
            
            response = request.execute()
            playlist_id = response['id']
            
            logger.info(f"Created YouTube playlist: {title} (ID: {playlist_id})")
            return playlist_id, None
            
        except HttpError as e:
            error_msg = f"Error creating playlist: {e}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error creating playlist: {e}"
            logger.error(error_msg)
            return None, error_msg
    
    def search_video(self, query, max_results=5):
        """Busca videos en YouTube"""
        try:
            if not self.youtube_service:
                return []
            
            request = self.youtube_service.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results,
                order="relevance"
            )
            
            response = request.execute()
            videos = []
            
            for item in response.get('items', []):
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['default']['url']
                })
            
            return videos
            
        except HttpError as e:
            logger.error(f"Error searching videos: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching videos: {e}")
            return []
    
    def add_video_to_playlist(self, playlist_id, video_id):
        """Añade un video a una playlist"""
        try:
            if not self.youtube_service:
                return False, "Servicio de YouTube no disponible"
            
            request = self.youtube_service.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            
            response = request.execute()
            logger.info(f"Added video {video_id} to playlist {playlist_id}")
            return True, None
            
        except HttpError as e:
            error_msg = f"Error adding video to playlist: {e}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error adding video to playlist: {e}"
            logger.error(error_msg)
            return False, error_msg
