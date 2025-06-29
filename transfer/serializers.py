from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Playlist, Song, TransferJob, PlaylistSong, SongTransferResult

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class SongSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='name', read_only=True)  # Alias para compatibilidad
    
    class Meta:
        model = Song
        fields = [
            'id', 'name', 'title', 'artist', 'album', 
            'spotify_id', 'youtube_video_id', 'duration_ms', 
            'preview_url', 'spotify_url'
        ]


class PlaylistSongSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    
    class Meta:
        model = PlaylistSong
        fields = ['id', 'song', 'position', 'added_at']


class PlaylistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    songs = PlaylistSongSerializer(source='playlistsong_set', many=True, read_only=True)
    spotify_url = serializers.ReadOnlyField()
    youtube_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Playlist
        fields = [
            'id', 'spotify_id', 'youtube_playlist_id', 'name', 'description', 'total_tracks',
            'created_at', 'updated_at', 'user', 'songs', 'spotify_url', 'youtube_url'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PlaylistListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar playlists sin las canciones"""
    user = UserSerializer(read_only=True)
    spotify_url = serializers.ReadOnlyField()
    youtube_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Playlist
        fields = [
            'id', 'spotify_id', 'youtube_playlist_id', 'name', 'description', 'total_tracks',
            'created_at', 'updated_at', 'user', 'spotify_url', 'youtube_url'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SongTransferResultSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    
    class Meta:
        model = SongTransferResult
        fields = [
            'id', 'song', 'transfer_status', 'youtube_video_id', 'youtube_title',
            'youtube_artist', 'match_confidence', 'error_message', 'processed_at'
        ]


class TransferJobSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    playlist = PlaylistListSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    song_results = SongTransferResultSerializer(many=True, read_only=True)
    
    class Meta:
        model = TransferJob
        fields = [
            'id', 'user', 'playlist', 'status', 'youtube_playlist_id',
            'youtube_playlist_name', 'total_songs', 'processed_songs',
            'successful_transfers', 'failed_transfers', 'progress_percentage',
            'created_at', 'started_at', 'completed_at', 'error_message',
            'notes', 'song_results'
        ]
        read_only_fields = [
            'created_at', 'started_at', 'completed_at', 'total_songs',
            'processed_songs', 'successful_transfers', 'failed_transfers'
        ]


class TransferJobListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar trabajos sin detalles de canciones"""
    user = UserSerializer(read_only=True)
    playlist = PlaylistListSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = TransferJob
        fields = [
            'id', 'user', 'playlist', 'status', 'youtube_playlist_id',
            'youtube_playlist_name', 'total_songs', 'processed_songs',
            'successful_transfers', 'failed_transfers', 'progress_percentage',
            'created_at', 'started_at', 'completed_at', 'error_message'
        ]


class TransferJobCreateSerializer(serializers.Serializer):
    """Serializer para crear nuevos trabajos de transferencia"""
    playlist_id = serializers.IntegerField()
    youtube_playlist_name = serializers.CharField(max_length=200)
    
    def validate_playlist_id(self, value):
        """Validar que la playlist existe y pertenece al usuario"""
        user = self.context['request'].user
        try:
            playlist = Playlist.objects.get(id=value, user=user)
            return value
        except Playlist.DoesNotExist:
            raise serializers.ValidationError("La playlist no existe o no te pertenece.")


class PlaylistImportSerializer(serializers.Serializer):
    """Serializer para importar playlists desde Spotify"""
    spotify_playlist_id = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer extendido para el perfil de usuario con información de Spotify"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'spotify_user_id', 'profile_image', 'country', 'spotify_premium',
            'auto_import_playlists', 'email_notifications', 'spotify_connected_at',
            'last_spotify_sync', 'has_spotify_connected', 'display_name'
        ]
        read_only_fields = ['spotify_user_id', 'spotify_connected_at', 'last_spotify_sync', 'has_spotify_connected', 'display_name']
