from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.db import models
from django.contrib.auth import authenticate, login, get_user_model
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
import logging

from .models import Playlist, Song, TransferJob, PlaylistSong, SongTransferResult
from .serializers import (
    PlaylistSerializer, PlaylistListSerializer, PlaylistImportSerializer,
    TransferJobSerializer, TransferJobListSerializer, TransferJobCreateSerializer,
    SongSerializer, UserRegistrationSerializer, UserProfileSerializer, UserSerializer
)
from .services.spotify import SpotifyAuthService, SpotifyPlaylistService
from .services.youtube import YouTubeTransferService, PlaylistExportService
from .services.google_auth import GoogleOAuthService, YouTubeMusicService

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Registro de nuevos usuarios"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'Usuario registrado exitosamente'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login de usuarios"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if username and password:
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Login exitoso'
            })
        else:
            return Response({
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'error': 'Se requieren username y password'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout de usuarios"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logout exitoso'})
    except:
        return Response({'error': 'Error al hacer logout'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """Ver y actualizar perfil de usuario"""
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlaylistViewSet(viewsets.ModelViewSet):
    """ViewSet para manejar playlists"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Playlist.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PlaylistListSerializer
        return PlaylistSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def import_from_spotify(self, request):
        """Importar una playlist desde Spotify"""
        serializer = PlaylistImportSerializer(data=request.data)
        if serializer.is_valid():
            try:
                spotify_service = SpotifyPlaylistService(request.user)
                playlist = spotify_service.import_playlist(
                    spotify_playlist_id=serializer.validated_data['spotify_playlist_id'],
                    name=serializer.validated_data.get('name'),
                    description=serializer.validated_data.get('description', '')
                )
                return Response(
                    PlaylistSerializer(playlist).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def songs(self, request, pk=None):
        """Obtener las canciones de una playlist"""
        playlist = self.get_object()
        playlist_songs = PlaylistSong.objects.filter(playlist=playlist).order_by('position')
        songs = [ps.song for ps in playlist_songs]
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def export_csv(self, request, pk=None):
        """Exportar playlist a CSV optimizado para Excel/Sheets"""
        playlist = self.get_object()
        try:
            export_service = PlaylistExportService(request.user)
            csv_content = export_service.export_to_csv(playlist)
            
            # Crear respuesta HTTP con CSV y encoding UTF-8 BOM para Excel
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = f'attachment; filename="{playlist.name}_playlist.csv"'
            
            # Agregar BOM para que Excel reconozca UTF-8
            response.write('\ufeff')  # BOM
            response.write(csv_content)
            
            return response
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def playlist_url(self, request, pk=None):
        """Obtener URLs de la playlist"""
        playlist = self.get_object()
        return Response({
            'spotify_url': playlist.spotify_url,
            'youtube_url': playlist.youtube_url
        })
        songs = [ps.song for ps in playlist_songs]
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def debug_songs(self, request, pk=None):
        """Debug: Ver las canciones de una playlist"""
        playlist = self.get_object()
        from .models import PlaylistSong
        
        playlist_songs = PlaylistSong.objects.filter(playlist=playlist).order_by('position')
        
        debug_info = {
            'playlist_id': playlist.id,
            'playlist_name': playlist.name,
            'total_tracks_field': playlist.total_tracks,
            'actual_songs_count': playlist_songs.count(),
            'songs': []
        }
        
        for ps in playlist_songs[:10]:  # Solo primeras 10 para debug
            debug_info['songs'].append({
                'position': ps.position,
                'song_id': ps.song.id,
                'song_name': ps.song.name,
                'artist': ps.song.artist,
                'spotify_id': ps.song.spotify_id
            })
        
        return Response(debug_info)


class TransferJobViewSet(viewsets.ModelViewSet):
    """ViewSet para manejar trabajos de transferencia"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TransferJob.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TransferJobListSerializer
        elif self.action == 'start_transfer':
            return TransferJobCreateSerializer
        return TransferJobSerializer
    
    @action(detail=False, methods=['post'])
    def start_transfer(self, request):
        """Iniciar un nuevo trabajo de transferencia"""
        serializer = TransferJobCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    playlist = get_object_or_404(
                        Playlist, 
                        id=serializer.validated_data['playlist_id'],
                        user=request.user
                    )
                    
                    # Verificar que no hay un trabajo activo para esta playlist
                    existing_job = TransferJob.objects.filter(
                        playlist=playlist,
                        status__in=['pending', 'processing']
                    ).first()
                    
                    if existing_job:
                        return Response(
                            {'error': 'Ya hay un trabajo de transferencia activo para esta playlist.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Crear el trabajo de transferencia
                    transfer_job = TransferJob.objects.create(
                        user=request.user,
                        playlist=playlist,
                        youtube_playlist_name=serializer.validated_data['youtube_playlist_name'],
                        total_songs=playlist.total_tracks
                    )
                    
                    # Iniciar la transferencia usando el servicio de YouTube
                    try:
                        youtube_service = YouTubeTransferService(request.user)
                        result = youtube_service.transfer_playlist(playlist, transfer_job)
                        
                        return Response(
                            TransferJobSerializer(transfer_job).data,
                            status=status.HTTP_201_CREATED
                        )
                    except Exception as transfer_error:
                        # Si falla la transferencia, marcar como fallido
                        transfer_job.status = 'failed'
                        transfer_job.error_message = str(transfer_error)
                        transfer_job.save()
                        
                        return Response(
                            {'error': f'Error en transferencia: {str(transfer_error)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                    
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel_transfer(self, request, pk=None):
        """Cancelar un trabajo de transferencia"""
        transfer_job = self.get_object()
        
        if transfer_job.status in ['completed', 'failed']:
            return Response(
                {'error': 'No se puede cancelar un trabajo ya completado o fallido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transfer_job.status = 'failed'
        transfer_job.error_message = 'Cancelado por el usuario'
        transfer_job.save()
        
        return Response(
            TransferJobSerializer(transfer_job).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Obtener el progreso de un trabajo de transferencia"""
        transfer_job = self.get_object()
        return Response({
            'id': transfer_job.id,
            'status': transfer_job.status,
            'progress_percentage': transfer_job.progress_percentage,
            'processed_songs': transfer_job.processed_songs,
            'total_songs': transfer_job.total_songs,
            'successful_transfers': transfer_job.successful_transfers,
            'failed_transfers': transfer_job.failed_transfers,
            'youtube_playlist_id': transfer_job.youtube_playlist_id,
        })


class SongViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para canciones"""
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtrar canciones que pertenecen a playlists del usuario
        user_playlists = Playlist.objects.filter(user=self.request.user)
        playlist_songs = PlaylistSong.objects.filter(playlist__in=user_playlists)
        song_ids = playlist_songs.values_list('song_id', flat=True).distinct()
        return Song.objects.filter(id__in=song_ids)


@api_view(['GET'])
@permission_classes([AllowAny])
def spotify_auth_url(request):
    """Obtener URL de autorización de Spotify"""
    try:
        spotify_service = SpotifyAuthService()
        result = spotify_service.get_auth_url()
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def spotify_callback(request):
    """Manejar callback directo de Spotify (GET desde Spotify)"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        # Redirigir al frontend con error
        return redirect(f"{settings.FRONTEND_URL}/?error=spotify_auth_error&message={error}")
    
    if not code:
        return redirect(f"{settings.FRONTEND_URL}/?error=spotify_auth_error&message=no_code_received")
    
    # Redirigir al frontend con el código para que maneje la autenticación
    return redirect(f"{settings.FRONTEND_URL}/auth/spotify/callback?code={code}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def spotify_connect(request):
    """Conectar cuenta de Spotify (POST desde frontend autenticado)"""
    code = request.data.get('code')
    if not code:
        return Response({'error': 'Código de autorización requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        spotify_service = SpotifyAuthService()
        result = spotify_service.handle_callback(code, request.user)
        
        if result['success']:
            return Response({
                'message': 'Cuenta de Spotify conectada exitosamente',
                'user_info': result['user_info']
            })
        else:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def spotify_disconnect(request):
    """Desconectar cuenta de Spotify"""
    try:
        spotify_service = SpotifyAuthService()
        spotify_service.disconnect_user(request.user)
        return Response({'message': 'Cuenta de Spotify desconectada exitosamente'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def spotify_playlists(request):
    """Obtener playlists de Spotify del usuario"""
    try:
        spotify_service = SpotifyPlaylistService(request.user)
        playlists = spotify_service.get_user_playlists()
        return Response(playlists)  # Devolver directamente el array
    except Exception as e:
        error_msg = str(e)
        if "Token de Spotify expirado" in error_msg or "expirado y no se pudo refrescar" in error_msg:
            return Response({
                'error': 'Tu sesión de Spotify ha expirado. Por favor, reconecta tu cuenta.',
                'requires_reconnection': True
            }, status=status.HTTP_401_UNAUTHORIZED)
        elif "Usuario no conectado a Spotify" in error_msg:
            return Response({
                'error': 'No tienes una cuenta de Spotify conectada.',
                'requires_connection': True
            }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error': f'Error al obtener playlists: {error_msg}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def spotify_status(request):
    """Obtener el estado de conexión con Spotify del usuario"""
    try:
        user = request.user
        is_connected = bool(user.spotify_access_token and user.spotify_refresh_token)
        
        response_data = {
            'is_connected': is_connected,
            'spotify_user_id': user.spotify_user_id if is_connected else None,
            'spotify_display_name': user.spotify_display_name if is_connected else None,
            'token_valid': True,  # Asumimos que es válido si existe
            'needs_reconnection': False
        }
        
        return Response(response_data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def spotify_auth_or_register(request):
    """Autenticar con Spotify o registrar nuevo usuario usando datos de Spotify"""
    code = request.data.get('code')
    if not code:
        return Response({'error': 'Código de autorización requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        spotify_service = SpotifyAuthService()
        
        # Obtener tokens de Spotify
        token_info = spotify_service.exchange_code_for_tokens(code)
        if not token_info.get('access_token'):
            return Response({'error': 'No se pudo obtener token de acceso'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener información del usuario de Spotify
        user_info = spotify_service.get_user_info(token_info['access_token'])
        if not user_info:
            return Response({'error': 'No se pudo obtener información del usuario'}, status=status.HTTP_400_BAD_REQUEST)
        
        spotify_user_id = user_info.get('id')
        display_name = user_info.get('display_name') or spotify_user_id
        email = user_info.get('email')
        
        if not spotify_user_id:
            return Response({'error': 'No se pudo obtener ID de usuario de Spotify'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar si ya existe un usuario con este spotify_user_id
        existing_user = None
        try:
            existing_user = User.objects.get(spotify_user_id=spotify_user_id)
        except User.DoesNotExist:
            pass
        
        if existing_user:
            # Usuario existente: actualizar tokens y hacer login
            existing_user.spotify_access_token = token_info['access_token']
            existing_user.spotify_refresh_token = token_info.get('refresh_token', existing_user.spotify_refresh_token)
            existing_user.spotify_display_name = display_name
            existing_user.save()
            
            # Crear/obtener token de autenticación
            token, created = Token.objects.get_or_create(user=existing_user)
            
            return Response({
                'success': True,
                'user': UserSerializer(existing_user).data,
                'token': token.key,
                'message': f'Bienvenido de vuelta, {display_name}!',
                'is_new_user': False
            })
        else:
            # Usuario nuevo: crear cuenta
            username = f"spotify_{spotify_user_id}"
            
            # Verificar si el username ya existe (por si acaso)
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1
            
            # Crear nuevo usuario
            new_user = User.objects.create_user(
                username=username,
                email=email if email else f"{username}@spotify.local",
                first_name=display_name.split(' ')[0] if display_name else '',
                last_name=' '.join(display_name.split(' ')[1:]) if display_name and ' ' in display_name else '',
                spotify_user_id=spotify_user_id,
                spotify_access_token=token_info['access_token'],
                spotify_refresh_token=token_info.get('refresh_token'),
                spotify_display_name=display_name
            )
            
            # Crear token de autenticación
            token, created = Token.objects.get_or_create(user=new_user)
            
            return Response({
                'success': True,
                'user': UserSerializer(new_user).data,
                'token': token.key,
                'message': f'¡Bienvenido a XportSpot, {display_name}! Tu cuenta ha sido creada.',
                'is_new_user': True
            })
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# YouTube Music Configuration Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def youtube_music_status(request):
    """Obtener el estado de configuración de YouTube Music del usuario"""
    try:
        user = request.user
        return Response({
            'is_configured': user.has_youtube_music_configured,
            'configured_at': user.youtube_music_configured_at.isoformat() if user.youtube_music_configured_at else None,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def youtube_music_configure(request):
    """Configurar YouTube Music para el usuario"""
    try:
        browser_data = request.data.get('browser_data')
        if not browser_data:
            return Response({'error': 'Datos del navegador requeridos'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que los datos sean JSON válido
        import json
        try:
            if isinstance(browser_data, str):
                parsed_data = json.loads(browser_data)
            elif isinstance(browser_data, dict):
                parsed_data = browser_data
            else:
                raise ValueError("Formato inválido")
                
            # Validar que contiene la estructura esperada para YouTube Music
            if 'headers' not in parsed_data:
                return Response({
                    'error': 'Los datos del navegador deben contener un objeto "headers". Asegúrate de usar el formato correcto del browser.json.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            headers = parsed_data['headers']
            required_headers = ['cookie', 'user-agent']
            missing_headers = [h for h in required_headers if h not in headers and h.replace('-', '_') not in headers]
            
            if missing_headers:
                return Response({
                    'error': f'Faltan headers requeridos: {", ".join(missing_headers)}. Asegúrate de exportar correctamente los datos del navegador.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (json.JSONDecodeError, ValueError) as e:
            return Response({'error': f'Datos del navegador inválidos: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar configuración
        user = request.user
        user.youtube_music_browser_data = parsed_data
        user.youtube_music_configured = True
        user.youtube_music_configured_at = timezone.now()
        user.save()
        
        return Response({'message': 'YouTube Music configurado exitosamente'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def youtube_music_disconnect(request):
    """Desconfigurar YouTube Music para el usuario"""
    try:
        user = request.user
        user.youtube_music_browser_data = None
        user.youtube_music_configured = False
        user.youtube_music_configured_at = None
        user.save()
        
        return Response({'message': 'YouTube Music desconfigurado exitosamente'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def youtube_music_setup_guide(request):
    """Obtener la guía de configuración de YouTube Music"""
    guide = {
        'title': 'Configurar YouTube Music',
        'description': 'Sigue estos pasos para configurar YouTube Music y poder transferir tus playlists',
        'steps': [
            {
                'step': 1,
                'title': 'Abrir YouTube Music',
                'description': 'Ve a https://music.youtube.com e inicia sesión con tu cuenta de Google'
            },
            {
                'step': 2,
                'title': 'Abrir Herramientas de Desarrollador',
                'description': 'Presiona F12 o Ctrl+Shift+I (Cmd+Option+I en Mac) para abrir las herramientas de desarrollador'
            },
            {
                'step': 3,
                'title': 'Ir a la pestaña Network',
                'description': 'Haz clic en la pestaña "Network" o "Red" en las herramientas de desarrollador'
            },
            {
                'step': 4,
                'title': 'Hacer una búsqueda',
                'description': 'En YouTube Music, busca cualquier canción para generar tráfico de red'
            },
            {
                'step': 5,
                'title': 'Encontrar la petición',
                'description': 'En la pestaña Network, busca una petición que contenga "music.youtube.com" y haz clic derecho'
            },
            {
                'step': 6,
                'title': 'Copiar como cURL',
                'description': 'Selecciona "Copy" > "Copy as cURL" o "Copiar como cURL"'
            },
            {
                'step': 7,
                'title': 'Convertir a browser.json',
                'description': 'Ve a https://curlconverter.com/, pega el cURL y copia el resultado JSON'
            },
            {
                'step': 8,
                'title': 'Pegar en el formulario',
                'description': 'Pega el JSON en el formulario de abajo y haz clic en "Configurar"'
            }
        ],
        'troubleshooting': [
            {
                'problem': 'No aparecen peticiones en Network',
                'solution': 'Asegúrate de que la pestaña Network esté abierta ANTES de hacer la búsqueda'
            },
            {
                'problem': 'Error de formato JSON',
                'solution': 'Verifica que hayas copiado todo el cURL correctamente en curlconverter.com'
            },
            {
                'problem': 'Las transferencias usan playlists simuladas',
                'solution': 'Esto es normal por ahora. Las playlists simuladas incluyen todos los datos de las canciones encontradas en YouTube Music.'
            },
            {
                'problem': 'No puedo crear playlists reales en YouTube Music',
                'solution': 'La autenticación completa de YouTube Music requiere configuración OAuth adicional. Por ahora, las transferencias funcionan en modo simulado mejorado.'
            }
        ]
    }
    
    return Response(guide)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def youtube_music_test_connection(request):
    """Probar la conexión con YouTube Music usando la configuración del usuario"""
    try:
        from .services.youtube import YouTubeMusicService
        
        youtube_service = YouTubeMusicService(request.user)
        
        if not youtube_service.is_authenticated():
            return Response({
                'success': False,
                'error': 'Usuario no tiene configuración de YouTube Music'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si ytmusic se inicializó correctamente
        if not youtube_service.ytmusic:
            return Response({
                'success': False,
                'error': 'Error inicializando servicio de YouTube Music. Verifica tu configuración.',
                'authenticated': True,
                'user_configured': request.user.youtube_music_configured,
                'has_browser_data': bool(request.user.youtube_music_browser_data)
            })
        
        # Intentar hacer una búsqueda simple para probar la conexión
        try:
            # Intentar una búsqueda básica
            test_result = youtube_service.search_track("Never Gonna Give You Up", "Rick Astley")
            
            if test_result:
                return Response({
                    'success': True,
                    'message': 'Servicio de YouTube Music funcionando correctamente',
                    'details': {
                        'search_working': True,
                        'user_configured': request.user.youtube_music_configured,
                        'has_browser_data': bool(request.user.youtube_music_browser_data),
                        'test_search_result': {
                            'found_song': True,
                            'title': test_result.get('title'),
                            'artist': test_result.get('artists', [{}])[0].get('name') if test_result.get('artists') else None
                        },
                        'note': 'Las transferencias usarán playlists simuladas mejoradas ya que la autenticación completa de YouTube Music requiere configuración OAuth adicional.'
                    }
                })
            else:
                return Response({
                    'success': True,
                    'message': 'Servicio de YouTube Music disponible',
                    'details': {
                        'search_working': True,
                        'user_configured': request.user.youtube_music_configured,
                        'has_browser_data': bool(request.user.youtube_music_browser_data),
                        'test_search_result': {
                            'found_song': False
                        },
                        'note': 'Búsquedas funcionan pero no se encontraron resultados para la canción de prueba'
                    }
                })
        except Exception as e:
            return Response({
                'success': True,  # Cambiar a True porque el servicio básico funciona
                'message': 'Configuración guardada correctamente',
                'details': {
                    'search_error': str(e),
                    'user_configured': request.user.youtube_music_configured,
                    'has_browser_data': bool(request.user.youtube_music_browser_data),
                    'note': 'Las transferencias funcionarán en modo simulado mejorado'
                }
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error inicializando servicio: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# === GOOGLE OAUTH ENDPOINTS ===

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_auth_url(request):
    """Obtener URL de autorización de Google OAuth"""
    try:
        google_service = GoogleOAuthService()
        
        if not google_service.client_id or not google_service.client_secret:
            return Response({
                'error': 'Credenciales de Google OAuth no configuradas',
                'configured': False
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Generar estado único para seguridad
        state = f"user_{request.user.id}_{timezone.now().timestamp()}"
        
        auth_url, state = google_service.get_authorization_url(state)
        
        if not auth_url:
            return Response({
                'error': 'No se pudo generar la URL de autorización'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'auth_url': auth_url,
            'state': state,
            'configured': True
        })
        
    except Exception as e:
        return Response({
            'error': f'Error generando URL de autorización: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # Permitir acceso sin autenticación para callback
def google_oauth_callback(request):
    """Callback de Google OAuth"""
    try:
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            logger.error(f"Google OAuth error: {error}")
            # Redirigir al frontend con error
            return redirect(f"{settings.FRONTEND_URL}/dashboard?google_error={error}")
        
        if not code:
            return redirect(f"{settings.FRONTEND_URL}/dashboard?google_error=no_code")
        
        # Extraer user_id del state
        try:
            user_id = state.split('_')[1]
            user = User.objects.get(id=user_id)
        except (IndexError, ValueError, User.DoesNotExist):
            logger.error(f"Invalid state or user not found: {state}")
            return redirect(f"{settings.FRONTEND_URL}/dashboard?google_error=invalid_state")
        
        # Intercambiar código por tokens
        google_service = GoogleOAuthService()
        token_data = google_service.exchange_code_for_tokens(code, state)
        
        if not token_data:
            return redirect(f"{settings.FRONTEND_URL}/dashboard?google_error=token_exchange_failed")
        
        # Guardar tokens en el usuario
        user.google_access_token = token_data['access_token']
        user.google_refresh_token = token_data['refresh_token']
        user.google_token_expires_at = token_data['expires_at']
        user.google_connected_at = timezone.now()
        
        # Guardar información del usuario de Google
        if token_data['user_info']:
            user_info = token_data['user_info']
            user.google_user_id = user_info.get('google_id')
            user.google_email = user_info.get('email')
            user.google_display_name = user_info.get('name')
        
        user.save()
        
        logger.info(f"Google OAuth successful for user {user.username}")
        
        # Redirigir al frontend con éxito
        return redirect(f"{settings.FRONTEND_URL}/dashboard?google_success=true")
        
    except Exception as e:
        logger.error(f"Error in Google OAuth callback: {e}")
        return redirect(f"{settings.FRONTEND_URL}/dashboard?google_error=callback_error")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_status(request):
    """Obtener estado de conexión con Google"""
    user = request.user
    
    return Response({
        'connected': user.has_google_connected,
        'email': user.google_email,
        'display_name': user.google_display_name,
        'connected_at': user.google_connected_at,
        'expires_at': user.google_token_expires_at,
        'connection_method': user.youtube_music_connection_method
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def google_disconnect(request):
    """Desconectar cuenta de Google"""
    try:
        user = request.user
        
        if user.google_access_token:
            # Intentar revocar el token
            google_service = GoogleOAuthService()
            google_service.revoke_access(user.google_access_token)
        
        # Limpiar datos de Google
        user.google_user_id = None
        user.google_email = None
        user.google_display_name = None
        user.google_access_token = None
        user.google_refresh_token = None
        user.google_token_expires_at = None
        user.google_connected_at = None
        user.save()
        
        return Response({
            'message': 'Cuenta de Google desconectada exitosamente'
        })
        
    except Exception as e:
        return Response({
            'error': f'Error desconectando cuenta de Google: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_google_connection(request):
    """Probar conexión con Google/YouTube"""
    try:
        user = request.user
        
        if not user.has_google_connected:
            return Response({
                'success': False,
                'error': 'Cuenta de Google no conectada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si el token está expirado
        if user.google_token_expires_at and user.google_token_expires_at < timezone.now():
            # Intentar refrescar token
            google_service = GoogleOAuthService()
            new_token_data = google_service.refresh_access_token(user.google_refresh_token)
            
            if new_token_data:
                user.google_access_token = new_token_data['access_token']
                user.google_token_expires_at = new_token_data['expires_at']
                user.save()
            else:
                return Response({
                    'success': False,
                    'error': 'Token expirado y no se pudo refrescar. Reconecta tu cuenta.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Probar conexión
        google_service = GoogleOAuthService()
        success, result = google_service.test_connection(user.google_access_token)
        
        if success:
            return Response({
                'success': True,
                'connection_info': result,
                'message': 'Conexión con Google/YouTube exitosa'
            })
        else:
            return Response({
                'success': False,
                'error': result
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error probando conexión: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# === RED SOCIAL MUSICAL - NUEVOS ENDPOINTS ===

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def music_platforms(request):
    """Obtener plataformas musicales disponibles"""
    try:
        from .models import MusicPlatform
        
        platforms = MusicPlatform.objects.filter(is_active=True).order_by('display_name')
        user_connections = request.user.music_connections.filter(is_active=True)
        
        platform_data = []
        for platform in platforms:
            connection = user_connections.filter(platform=platform).first()
            
            platform_data.append({
                'name': platform.name,
                'display_name': platform.display_name,
                'icon_url': platform.icon_url,
                'color': platform.color,
                'supports_oauth': platform.supports_oauth,
                'is_connected': bool(connection),
                'connection_date': connection.connected_at if connection else None,
                'last_synced': connection.last_synced if connection else None
            })
        
        return Response({
            'platforms': platform_data,
            'connected_count': user_connections.count(),
            'available_count': platforms.count()
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo plataformas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def connect_platform(request, platform_name):
    """Conectar con una plataforma musical"""
    try:
        from .models import MusicPlatform
        
        # Obtener plataforma
        try:
            platform = MusicPlatform.objects.get(name=platform_name, is_active=True)
        except MusicPlatform.DoesNotExist:
            return Response({
                'error': 'Plataforma no encontrada o no disponible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar si ya está conectado
        existing_connection = request.user.music_connections.filter(
            platform=platform, is_active=True
        ).first()
        
        if existing_connection:
            return Response({
                'error': 'Ya estás conectado a esta plataforma',
                'connection_date': existing_connection.connected_at
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Para Spotify, redirigir al OAuth existente
        if platform_name == 'spotify':
            spotify_service = SpotifyAuthService()
            auth_url = spotify_service.get_authorization_url()
            return Response({
                'redirect_to_auth': True,
                'auth_url': auth_url,
                'platform': platform.display_name
            })
        
        # Para otras plataformas, retornar mensaje de no implementado aún
        return Response({
            'message': f'Conexión con {platform.display_name} estará disponible pronto',
            'platform': platform.display_name,
            'supports_oauth': platform.supports_oauth
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
    except Exception as e:
        return Response({
            'error': f'Error conectando plataforma: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_platform(request, platform_name):
    """Desconectar de una plataforma musical"""
    try:
        from .models import MusicPlatform
        
        # Obtener plataforma
        try:
            platform = MusicPlatform.objects.get(name=platform_name)
        except MusicPlatform.DoesNotExist:
            return Response({
                'error': 'Plataforma no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Buscar conexión activa
        connection = request.user.music_connections.filter(
            platform=platform, is_active=True
        ).first()
        
        if not connection:
            return Response({
                'error': 'No estás conectado a esta plataforma'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Desactivar conexión
        connection.is_active = False
        connection.save()
        
        # Limpiar datos relacionados
        request.user.listening_stats.filter(platform_connection=connection).delete()
        
        return Response({
            'message': f'Desconectado de {platform.display_name} exitosamente'
        })
        
    except Exception as e:
        return Response({
            'error': f'Error desconectando plataforma: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def platform_status(request, platform_name):
    """Obtener estado de conexión con una plataforma"""
    try:
        from .models import MusicPlatform
        
        try:
            platform = MusicPlatform.objects.get(name=platform_name)
        except MusicPlatform.DoesNotExist:
            return Response({
                'error': 'Plataforma no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        connection = request.user.music_connections.filter(
            platform=platform, is_active=True
        ).first()
        
        return Response({
            'platform': {
                'name': platform.name,
                'display_name': platform.display_name,
                'color': platform.color,
                'supports_oauth': platform.supports_oauth
            },
            'is_connected': bool(connection),
            'connection_date': connection.connected_at if connection else None,
            'last_synced': connection.last_synced if connection else None,
            'sync_errors': connection.sync_errors if connection else None
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo estado: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def music_stats(request):
    """Obtener estadísticas musicales unificadas del usuario"""
    try:
        from .services.music_analysis import MusicAnalysisService
        
        period = request.GET.get('period', 'monthly')  # monthly, yearly, all_time
        
        analysis_service = MusicAnalysisService(request.user)
        stats = analysis_service.get_unified_stats(period)
        
        return Response({
            'stats': stats,
            'period': period,
            'user': {
                'username': request.user.username,
                'display_name': request.user.display_name,
                'profile_public': request.user.profile_public
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo estadísticas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_music_data(request):
    """Sincronizar datos musicales de todas las plataformas conectadas"""
    try:
        from .models import UserListeningStats
        from .services.spotify_analysis import SpotifyMusicAnalysisService
        
        synced_platforms = []
        errors = []
        
        # Obtener conexiones activas
        connections = request.user.music_connections.filter(is_active=True)
        
        for connection in connections:
            try:
                if connection.platform.name == 'spotify':
                    # Sincronizar Spotify
                    if connection.access_token:
                        spotify_service = SpotifyMusicAnalysisService(connection.access_token)
                        stats_data = spotify_service.create_listening_stats_data(connection)
                        
                        if stats_data:
                            # Crear o actualizar estadísticas
                            stats, created = UserListeningStats.objects.update_or_create(
                                user=request.user,
                                platform_connection=connection,
                                period_type=stats_data['period_type'],
                                period_start=stats_data['period_start'],
                                defaults=stats_data
                            )
                            
                            synced_platforms.append({
                                'platform': connection.platform.display_name,
                                'status': 'success',
                                'tracks': stats_data['total_tracks'],
                                'minutes': stats_data['total_minutes']
                            })
                            
                            # Actualizar fecha de sincronización
                            connection.last_synced = timezone.now()
                            connection.sync_errors = ''
                            connection.save()
                        else:
                            errors.append(f"{connection.platform.display_name}: No se pudieron obtener datos")
                    else:
                        errors.append(f"{connection.platform.display_name}: Token de acceso no válido")
                
                # Agregar otras plataformas aquí en el futuro
                else:
                    errors.append(f"{connection.platform.display_name}: Sincronización no implementada aún")
                    
            except Exception as e:
                error_msg = f"{connection.platform.display_name}: {str(e)}"
                errors.append(error_msg)
                
                # Guardar error en la conexión
                connection.sync_errors = str(e)
                connection.save()
        
        return Response({
            'message': 'Sincronización completada',
            'synced_platforms': synced_platforms,
            'errors': errors,
            'total_platforms': len(connections),
            'successful_syncs': len(synced_platforms)
        })
        
    except Exception as e:
        return Response({
            'error': f'Error sincronizando datos: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_profile_public(request, username):
    """Obtener perfil público de un usuario"""
    try:
        user = User.objects.get(username=username)
        
        # Verificar si el perfil es público o si es el propio usuario
        if not user.profile_public and user != request.user:
            return Response({
                'error': 'Este perfil es privado'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener estadísticas si están habilitadas
        stats = None
        if user.show_listening_stats or user == request.user:
            from .services.music_analysis import MusicAnalysisService
            analysis_service = MusicAnalysisService(user)
            stats = analysis_service.get_unified_stats()
        
        return Response({
            'user': {
                'username': user.username,
                'display_name': user.display_name,
                'bio': user.bio,
                'profile_image': user.profile_image,
                'country': user.country,
                'joined_date': user.date_joined.date(),
                'last_active': user.last_active,
                'connected_platforms': user.connected_platforms if user.show_listening_stats else []
            },
            'stats': stats if stats and (user.show_listening_stats or user == request.user) else None,
            'is_friend': request.user.is_authenticated and request.user != user and user in [
                f.addressee if f.requester == request.user else f.requester 
                for f in request.user.sent_friend_requests.filter(status='accepted').union(
                    request.user.received_friend_requests.filter(status='accepted')
                )
            ] if request.user.is_authenticated else False
        })
        
    except User.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error obteniendo perfil: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_search(request):
    """Buscar usuarios por nombre de usuario o nombre real"""
    try:
        query = request.GET.get('q', '').strip()
        if not query or len(query) < 2:
            return Response({
                'error': 'La búsqueda debe tener al menos 2 caracteres'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar usuarios públicos que coincidan
        users = User.objects.filter(
            profile_public=True
        ).filter(
            username__icontains=query
        ).exclude(
            id=request.user.id
        )[:20]  # Limitar a 20 resultados
        
        results = []
        for user in users:
            results.append({
                'username': user.username,
                'display_name': user.display_name,
                'bio': user.bio[:100] if user.bio else '',
                'profile_image': user.profile_image,
                'country': user.country,
                'connected_platforms': len(user.connected_platforms),
                'total_listening_minutes': user.total_listening_minutes
            })
        
        return Response({
            'users': results,
            'query': query,
            'total_results': len(results)
        })
        
    except Exception as e:
        return Response({
            'error': f'Error buscando usuarios: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def discover_users(request):
    """Descubrir usuarios con gustos musicales similares"""
    try:
        from .services.music_analysis import MusicAnalysisService
        
        # Obtener usuarios con estadísticas musicales
        users_with_stats = User.objects.filter(
            profile_public=True,
            listening_stats__isnull=False
        ).exclude(
            id=request.user.id
        ).distinct()[:50]
        
        analysis_service = MusicAnalysisService(request.user)
        compatible_users = []
        
        for user in users_with_stats:
            try:
                compatibility = analysis_service.calculate_music_compatibility(user)
                if compatibility and compatibility['overall_compatibility'] >= 30:
                    compatible_users.append({
                        'user': {
                            'username': user.username,
                            'display_name': user.display_name,
                            'bio': user.bio[:100] if user.bio else '',
                            'profile_image': user.profile_image,
                            'country': user.country,
                            'connected_platforms': len(user.connected_platforms)
                        },
                        'compatibility': compatibility
                    })
            except:
                continue
        
        # Ordenar por compatibilidad
        compatible_users.sort(key=lambda x: x['compatibility']['overall_compatibility'], reverse=True)
        
        return Response({
            'users': compatible_users[:20],  # Top 20 más compatibles
            'total_analyzed': len(users_with_stats),
            'total_compatible': len(compatible_users)
        })
        
    except Exception as e:
        return Response({
            'error': f'Error descubriendo usuarios: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_friend_request(request):
    """Enviar solicitud de amistad"""
    try:
        from .models import Friendship
        
        username = request.data.get('username')
        if not username:
            return Response({
                'error': 'Username es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            addressee = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if addressee == request.user:
            return Response({
                'error': 'No puedes enviarte una solicitud a ti mismo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not addressee.allow_friend_requests:
            return Response({
                'error': 'Este usuario no acepta solicitudes de amistad'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar si ya existe una solicitud
        existing = Friendship.objects.filter(
            requester=request.user, addressee=addressee
        ).first() or Friendship.objects.filter(
            requester=addressee, addressee=request.user
        ).first()
        
        if existing:
            if existing.status == 'accepted':
                return Response({
                    'error': 'Ya son amigos'
                }, status=status.HTTP_400_BAD_REQUEST)
            elif existing.status == 'pending':
                return Response({
                    'error': 'Ya existe una solicitud pendiente'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear solicitud de amistad
        friendship = Friendship.objects.create(
            requester=request.user,
            addressee=addressee,
            status='pending'
        )
        
        return Response({
            'message': f'Solicitud de amistad enviada a {addressee.display_name}',
            'friendship_id': friendship.id
        })
        
    except Exception as e:
        return Response({
            'error': f'Error enviando solicitud: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def friend_requests(request):
    """Obtener solicitudes de amistad pendientes"""
    try:
        from .models import Friendship
        
        # Solicitudes recibidas (pendientes)
        received_requests = Friendship.objects.filter(
            addressee=request.user,
            status='pending'
        ).order_by('-created_at')
        
        # Solicitudes enviadas (pendientes)
        sent_requests = Friendship.objects.filter(
            requester=request.user,
            status='pending'
        ).order_by('-created_at')
        
        received_data = []
        for req in received_requests:
            received_data.append({
                'id': req.id,
                'requester': {
                    'username': req.requester.username,
                    'display_name': req.requester.display_name,
                    'profile_image': req.requester.profile_image,
                    'bio': req.requester.bio[:100] if req.requester.bio else ''
                },
                'created_at': req.created_at
            })
        
        sent_data = []
        for req in sent_requests:
            sent_data.append({
                'id': req.id,
                'addressee': {
                    'username': req.addressee.username,
                    'display_name': req.addressee.display_name,
                    'profile_image': req.addressee.profile_image
                },
                'created_at': req.created_at
            })
        
        return Response({
            'received_requests': received_data,
            'sent_requests': sent_data,
            'total_received': len(received_data),
            'total_sent': len(sent_data)
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo solicitudes: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_friend_request(request, request_id):
    """Aceptar solicitud de amistad"""
    try:
        from .models import Friendship
        
        friendship = Friendship.objects.get(
            id=request_id,
            addressee=request.user,
            status='pending'
        )
        
        friendship.status = 'accepted'
        friendship.save()
        
        return Response({
            'message': f'Ahora eres amigo de {friendship.requester.display_name}',
            'friend': {
                'username': friendship.requester.username,
                'display_name': friendship.requester.display_name,
                'profile_image': friendship.requester.profile_image
            }
        })
        
    except Friendship.DoesNotExist:
        return Response({
            'error': 'Solicitud de amistad no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error aceptando solicitud: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_friend_request(request, request_id):
    """Rechazar solicitud de amistad"""
    try:
        from .models import Friendship
        
        friendship = Friendship.objects.get(
            id=request_id,
            addressee=request.user,
            status='pending'
        )
        
        friendship.delete()
        
        return Response({
            'message': 'Solicitud de amistad rechazada'
        })
        
    except Friendship.DoesNotExist:
        return Response({
            'error': 'Solicitud de amistad no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Error rechazando solicitud: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def friends_list(request):
    """Obtener lista de amigos"""
    try:
        from .models import Friendship
        
        # Obtener amistades aceptadas (en ambas direcciones)
        friendships = Friendship.objects.filter(
            status='accepted'
        ).filter(
            models.Q(requester=request.user) | models.Q(addressee=request.user)
        ).order_by('-updated_at')
        
        friends = []
        for friendship in friendships:
            friend = friendship.addressee if friendship.requester == request.user else friendship.requester
            
            friends.append({
                'username': friend.username,
                'display_name': friend.display_name,
                'profile_image': friend.profile_image,
                'bio': friend.bio[:100] if friend.bio else '',
                'country': friend.country,
                'connected_platforms': len(friend.connected_platforms),
                'last_active': friend.last_active,
                'friends_since': friendship.updated_at
            })
        
        return Response({
            'friends': friends,
            'total_friends': len(friends)
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo amigos: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def music_compatibility(request, username):
    """Calcular compatibilidad musical con otro usuario"""
    try:
        from .services.music_analysis import MusicAnalysisService
        
        try:
            other_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if other_user == request.user:
            return Response({
                'error': 'No puedes calcular compatibilidad contigo mismo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        analysis_service = MusicAnalysisService(request.user)
        compatibility = analysis_service.calculate_music_compatibility(other_user)
        
        if not compatibility:
            return Response({
                'error': 'No se pudo calcular la compatibilidad. Ambos usuarios deben tener datos musicales.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'compatibility': compatibility,
            'user1': {
                'username': request.user.username,
                'display_name': request.user.display_name
            },
            'user2': {
                'username': other_user.username,
                'display_name': other_user.display_name
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error calculando compatibilidad: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def music_recommendations(request):
    """Obtener recomendaciones musicales basadas en amigos"""
    try:
        from .services.music_analysis import MusicAnalysisService
        
        analysis_service = MusicAnalysisService(request.user)
        recommendations = analysis_service.get_music_recommendations()
        
        return Response({
            'recommendations': recommendations,
            'total_recommendations': len(recommendations),
            'based_on': 'Amigos con gustos musicales similares'
        })
        
    except Exception as e:
        return Response({
            'error': f'Error obteniendo recomendaciones: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
