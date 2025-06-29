from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Modelo de usuario para la red social musical multiplataforma"""
    
    # Información del perfil social
    bio = models.TextField(max_length=500, blank=True)
    profile_image = models.URLField(blank=True, null=True)
    country = models.CharField(max_length=10, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    
    # Configuraciones de privacidad
    profile_public = models.BooleanField(default=True)
    show_listening_stats = models.BooleanField(default=True)
    show_top_artists = models.BooleanField(default=True)
    show_top_genres = models.BooleanField(default=True)
    allow_friend_requests = models.BooleanField(default=True)
    
    # Configuraciones de notificaciones
    email_notifications = models.BooleanField(default=True)
    friend_requests_notifications = models.BooleanField(default=True)
    music_recommendations_notifications = models.BooleanField(default=True)
    
    # Timestamps
    last_music_sync = models.DateTimeField(blank=True, null=True)
    last_active = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username
    
    @property
    def display_name(self):
        return self.get_full_name() or self.username
    
    @property
    def connected_platforms(self):
        """Retorna lista de plataformas conectadas"""
        platforms = []
        connections = self.music_connections.all()
        return [conn.platform for conn in connections if conn.is_active]
    
    @property
    def total_listening_minutes(self):
        """Total de minutos escuchados en todas las plataformas"""
        return self.listening_stats.aggregate(
            total=models.Sum('total_minutes')
        )['total'] or 0


class MusicPlatform(models.Model):
    """Plataformas de música soportadas"""
    PLATFORM_CHOICES = [
        ('spotify', 'Spotify'),
        ('youtube_music', 'YouTube Music'),
        ('soundcloud', 'SoundCloud'),
        ('apple_music', 'Apple Music'),
        ('deezer', 'Deezer'),
        ('tidal', 'Tidal'),
        ('amazon_music', 'Amazon Music'),
        ('pandora', 'Pandora'),
    ]
    
    name = models.CharField(max_length=50, choices=PLATFORM_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    icon_url = models.URLField(blank=True)
    color = models.CharField(max_length=7, default='#1DB954')  # Color hex
    is_active = models.BooleanField(default=True)
    supports_oauth = models.BooleanField(default=False)
    api_documentation_url = models.URLField(blank=True)
    
    def __str__(self):
        return self.display_name
    
    class Meta:
        ordering = ['display_name']


class UserMusicConnection(models.Model):
    """Conexiones de usuarios con plataformas de música"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='music_connections')
    platform = models.ForeignKey(MusicPlatform, on_delete=models.CASCADE)
    
    # Datos de OAuth
    platform_user_id = models.CharField(max_length=200)
    platform_username = models.CharField(max_length=200, blank=True)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)
    
    # Datos del perfil de la plataforma
    profile_data = models.JSONField(default=dict)  # Datos específicos de cada plataforma
    
    # Estado de la conexión
    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(blank=True, null=True)
    sync_errors = models.TextField(blank=True)
    
    # Timestamps
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.platform.display_name}"
    
    class Meta:
        unique_together = ['user', 'platform']
        ordering = ['-connected_at']


class Artist(models.Model):
    """Artistas unificados de todas las plataformas"""
    name = models.CharField(max_length=300)
    
    # IDs en diferentes plataformas
    spotify_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    youtube_music_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    soundcloud_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    apple_music_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    
    # Metadatos
    genres = models.JSONField(default=list)  # Lista de géneros
    image_url = models.URLField(blank=True)
    popularity_score = models.IntegerField(default=0)  # 0-100
    
    # Análisis
    total_listeners = models.IntegerField(default=0)
    monthly_listeners = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Genre(models.Model):
    """Géneros musicales"""
    name = models.CharField(max_length=100, unique=True)
    parent_genre = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    color = models.CharField(max_length=7, default='#8B5CF6')  # Color hex para visualización
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class UserListeningStats(models.Model):
    """Estadísticas de escucha por usuario y plataforma"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listening_stats')
    platform_connection = models.ForeignKey(UserMusicConnection, on_delete=models.CASCADE)
    
    # Período de análisis
    period_type = models.CharField(max_length=20, choices=[
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('yearly', 'Anual'),
        ('all_time', 'Todo el tiempo')
    ])
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Estadísticas generales
    total_minutes = models.IntegerField(default=0)
    total_tracks = models.IntegerField(default=0)
    unique_artists = models.IntegerField(default=0)
    unique_albums = models.IntegerField(default=0)
    
    # Top datos (almacenados como JSON)
    top_artists = models.JSONField(default=list)  # [{"name": "Artist", "minutes": 120, "plays": 45}]
    top_genres = models.JSONField(default=list)
    top_tracks = models.JSONField(default=list)
    
    # Patrones de escucha
    listening_patterns = models.JSONField(default=dict)  # Por hora del día, día de semana, etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.platform_connection.platform.display_name} - {self.period_type}"
    
    class Meta:
        unique_together = ['user', 'platform_connection', 'period_type', 'period_start']
        ordering = ['-period_end']


class Friendship(models.Model):
    """Sistema de amistad entre usuarios"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('blocked', 'Bloqueada'),
    ]
    
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    addressee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.requester.username} -> {self.addressee.username} ({self.status})"
    
    class Meta:
        unique_together = ['requester', 'addressee']
        ordering = ['-created_at']


class MusicCompatibility(models.Model):
    """Compatibilidad musical entre usuarios"""
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compatibility_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compatibility_as_user2')
    
    # Puntuaciones de compatibilidad (0-100)
    overall_compatibility = models.FloatField(default=0.0)
    artist_compatibility = models.FloatField(default=0.0)
    genre_compatibility = models.FloatField(default=0.0)
    
    # Detalles de compatibilidad
    shared_artists = models.JSONField(default=list)
    shared_genres = models.JSONField(default=list)
    compatibility_details = models.JSONField(default=dict)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user1.username} <-> {self.user2.username} ({self.overall_compatibility:.1f}%)"
    
    class Meta:
        unique_together = ['user1', 'user2']
        ordering = ['-overall_compatibility']


# === MODELOS LEGACY (mantenidos para compatibilidad) ===

class Playlist(models.Model):
    """Modelo legacy para playlists - mantenido para compatibilidad"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=100, unique=True)
    youtube_playlist_id = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    total_tracks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.total_tracks} canciones)"
    
    @property
    def spotify_url(self):
        return f"https://open.spotify.com/playlist/{self.spotify_id}"
    
    @property 
    def youtube_url(self):
        if self.youtube_playlist_id:
            return f"https://music.youtube.com/playlist?list={self.youtube_playlist_id}"
        return None
    
    class Meta:
        ordering = ['-created_at']


class Song(models.Model):
    """Modelo legacy para canciones - mantenido para compatibilidad"""
    name = models.CharField(max_length=300)
    artist = models.CharField(max_length=300)
    album = models.CharField(max_length=300, blank=True)
    spotify_id = models.CharField(max_length=100, blank=True)
    youtube_video_id = models.CharField(max_length=50, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    preview_url = models.URLField(blank=True, null=True)
    spotify_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.artist}"
    
    @property
    def title(self):
        """Alias para name para compatibilidad"""
        return self.name
    
    class Meta:
        unique_together = ['name', 'artist']


class PlaylistSong(models.Model):
    """Modelo legacy para la relación entre playlist y canciones"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    position = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['playlist', 'song', 'position']
        ordering = ['position']


class TransferJob(models.Model):
    """Modelo legacy para trabajos de transferencia"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('partial', 'Parcialmente completado'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    youtube_playlist_id = models.CharField(max_length=100, blank=True)
    youtube_playlist_name = models.CharField(max_length=200, blank=True)
    
    # Estadísticas del trabajo
    total_songs = models.IntegerField(default=0)
    processed_songs = models.IntegerField(default=0)
    successful_transfers = models.IntegerField(default=0)
    failed_transfers = models.IntegerField(default=0)
    progress_percentage = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Mensajes y errores
    error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Transferencia de '{self.playlist.name}' - {self.status}"
    
    @property
    def progress_percent(self):
        """Alias para compatibilidad"""
        return self.progress_percentage
    
    def start_processing(self):
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save()
    
    def complete_processing(self):
        self.status = 'completed' if self.failed_transfers == 0 else 'partial'
        self.completed_at = timezone.now()
        self.save()
    
    class Meta:
        ordering = ['-created_at']


class SongTransferResult(models.Model):
    """Modelo legacy para resultados de transferencia"""
    transfer_job = models.ForeignKey(TransferJob, on_delete=models.CASCADE, related_name='song_results')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    
    # Estados de transferencia
    STATUS_CHOICES = [
        ('success', 'Exitoso'),
        ('failed', 'Fallido'),
        ('not_found', 'No encontrado'),
    ]
    
    transfer_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='failed')
    youtube_video_id = models.CharField(max_length=50, blank=True, null=True)
    youtube_title = models.CharField(max_length=300, blank=True, null=True)
    youtube_artist = models.CharField(max_length=300, blank=True, null=True)
    match_confidence = models.FloatField(default=0.0)
    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.song.name} - {self.transfer_status}"
    
    class Meta:
        unique_together = ['transfer_job', 'song']