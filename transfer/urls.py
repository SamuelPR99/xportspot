from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    PlaylistViewSet, TransferJobViewSet, SongViewSet,
    register, login_view, logout_view, profile_view,
    spotify_auth_url, spotify_callback, spotify_connect, spotify_disconnect, spotify_playlists, spotify_status,
    spotify_auth_or_register,
    youtube_music_status, youtube_music_configure, youtube_music_disconnect, youtube_music_setup_guide,
    youtube_music_test_connection,
    google_auth_url, google_oauth_callback, google_status, google_disconnect, test_google_connection,
    # Nuevos endpoints para red social musical
    music_platforms, connect_platform, disconnect_platform, platform_status,
    music_stats, sync_music_data, user_profile_public, users_search,
    send_friend_request, friend_requests, accept_friend_request, decline_friend_request,
    friends_list, music_compatibility, music_recommendations, discover_users
)

# Crear el router y registrar los viewsets
router = DefaultRouter()
router.register(r'playlists', PlaylistViewSet, basename='playlist')
router.register(r'transfer-jobs', TransferJobViewSet, basename='transferjob')
router.register(r'songs', SongViewSet, basename='song')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Autenticación personalizada
    path('auth/register/', register, name='register'),
    path('auth/login/', login_view, name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/profile/', profile_view, name='profile'),
    
    # Autenticación con Spotify
    path('auth/spotify/url/', spotify_auth_url, name='spotify_auth_url'),
    path('auth/spotify/callback/', spotify_callback, name='spotify_callback'),  # Para callback directo de Spotify
    path('auth/spotify/connect/', spotify_connect, name='spotify_connect'),      # Para conectar desde frontend
    path('auth/spotify/auth-or-register/', spotify_auth_or_register, name='spotify_auth_or_register'),  # Login/registro con Spotify
    path('auth/spotify/disconnect/', spotify_disconnect, name='spotify_disconnect'),
    path('auth/spotify/status/', spotify_status, name='spotify_status'),
    path('auth/spotify/playlists/', spotify_playlists, name='spotify_playlists'),
    
    # Google OAuth (YouTube Music oficial)
    path('auth/google/url/', google_auth_url, name='google_auth_url'),
    path('auth/google/callback/', google_oauth_callback, name='google_oauth_callback'),
    path('auth/google/status/', google_status, name='google_status'),
    path('auth/google/disconnect/', google_disconnect, name='google_disconnect'),
    path('auth/google/test-connection/', test_google_connection, name='test_google_connection'),
    
    # === RED SOCIAL MUSICAL ===
    
    # Plataformas musicales
    path('music/platforms/', music_platforms, name='music_platforms'),
    path('music/platforms/<str:platform_name>/connect/', connect_platform, name='connect_platform'),
    path('music/platforms/<str:platform_name>/disconnect/', disconnect_platform, name='disconnect_platform'),
    path('music/platforms/<str:platform_name>/status/', platform_status, name='platform_status'),
    
    # Análisis musical
    path('music/stats/', music_stats, name='music_stats'),
    path('music/sync/', sync_music_data, name='sync_music_data'),
    path('music/recommendations/', music_recommendations, name='music_recommendations'),
    
    # Perfiles y usuarios
    path('users/profile/<str:username>/', user_profile_public, name='user_profile_public'),
    path('users/search/', users_search, name='users_search'),
    path('users/discover/', discover_users, name='discover_users'),
    
    # Sistema de amistad
    path('friends/send-request/', send_friend_request, name='send_friend_request'),
    path('friends/requests/', friend_requests, name='friend_requests'),
    path('friends/requests/<int:request_id>/accept/', accept_friend_request, name='accept_friend_request'),
    path('friends/requests/<int:request_id>/decline/', decline_friend_request, name='decline_friend_request'),
    path('friends/list/', friends_list, name='friends_list'),
    
    # Compatibilidad musical
    path('music/compatibility/<str:username>/', music_compatibility, name='music_compatibility'),
    
    # === LEGACY ENDPOINTS ===
    
    # === LEGACY ENDPOINTS ===
    
    # Spotify (legacy - mantenido para compatibilidad)
    path('auth/spotify/playlists/', spotify_playlists, name='spotify_playlists'),
    
    # YouTube Music Configuration (legacy)
    path('auth/youtube-music/status/', youtube_music_status, name='youtube_music_status'),
    path('auth/youtube-music/configure/', youtube_music_configure, name='youtube_music_configure'),
    path('auth/youtube-music/disconnect/', youtube_music_disconnect, name='youtube_music_disconnect'),
    path('auth/youtube-music/setup-guide/', youtube_music_setup_guide, name='youtube_music_setup_guide'),
    path('auth/youtube-music/test-connection/', youtube_music_test_connection, name='youtube_music_test_connection'),
    
    # Autenticación
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('auth/drf/', include('rest_framework.urls')),
]
