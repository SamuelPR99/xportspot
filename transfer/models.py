from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Playlist(models.Model):
    """Modelo para representar una playlist de Spotify"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    total_tracks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.total_tracks} canciones)"
    
    class Meta:
        ordering = ['-created_at']


class Song(models.Model):
    """Modelo para representar una canción"""
    title = models.CharField(max_length=300)
    artist = models.CharField(max_length=300)
    album = models.CharField(max_length=300, blank=True)
    spotify_track_id = models.CharField(max_length=100, blank=True)
    youtube_video_id = models.CharField(max_length=50, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.artist}"
    
    class Meta:
        unique_together = ['title', 'artist']


class PlaylistSong(models.Model):
    """Modelo para la relación entre playlist y canciones"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    position = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['playlist', 'song', 'position']
        ordering = ['position']


class TransferJob(models.Model):
    """Modelo para manejar trabajos de transferencia de playlists"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('partial', 'Parcialmente completado'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    youtube_playlist_id = models.CharField(max_length=100, blank=True)
    youtube_playlist_name = models.CharField(max_length=200, blank=True)
    
    # Estadísticas del trabajo
    total_songs = models.IntegerField(default=0)
    processed_songs = models.IntegerField(default=0)
    successful_transfers = models.IntegerField(default=0)
    failed_transfers = models.IntegerField(default=0)
    
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
    def progress_percentage(self):
        if self.total_songs == 0:
            return 0
        return int((self.processed_songs / self.total_songs) * 100)
    
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
    """Modelo para guardar los resultados de transferencia de cada canción"""
    transfer_job = models.ForeignKey(TransferJob, on_delete=models.CASCADE, related_name='song_results')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    
    SUCCESS = 'success'
    FAILED = 'failed'
    DUPLICATE = 'duplicate'
    NOT_FOUND = 'not_found'
    
    STATUS_CHOICES = [
        (SUCCESS, 'Exitoso'),
        (FAILED, 'Fallido'),
        (DUPLICATE, 'Duplicado'),
        (NOT_FOUND, 'No encontrado'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    youtube_video_id = models.CharField(max_length=50, blank=True)
    search_query = models.CharField(max_length=500)
    error_message = models.TextField(blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.song.title} - {self.status}"
    
    class Meta:
        unique_together = ['transfer_job', 'song'] 