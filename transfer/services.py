import logging
import threading
from typing import Optional
from django.utils import timezone
from django.conf import settings
from ytmusicapi import YTMusic

from .models import Playlist, Song, TransferJob, PlaylistSong, SongTransferResult

logger = logging.getLogger(__name__)


class SpotifyService:
    """Servicio para integrar con Spotify API"""
    
    def __init__(self):
        # Aquí integrarás la API de Spotify cuando la tengas
        pass
    
    def import_playlist(self, user, spotify_playlist_id, name=None, description=''):
        """
        Importar una playlist desde Spotify
        Por ahora es un método placeholder - aquí integrarás spotipy
        """
        # TODO: Implementar con spotipy
        # Por ahora crear datos de ejemplo
        playlist = Playlist.objects.create(
            user=user,
            spotify_id=spotify_playlist_id,
            name=name or "Playlist importada",
            description=description,
            total_tracks=0
        )
        return playlist


class YouTubeTransferService:
    """Servicio que integra tu lógica de PaYoutubeMusic.py"""
    
    def __init__(self):
        # Inicializar YouTube Music API con tu archivo browser.json
        try:
            self.ytmusic = YTMusic('browser.json')
        except Exception as e:
            logger.error(f"Error inicializando YTMusic: {e}")
            self.ytmusic = None
    
    def start_transfer_async(self, transfer_job_id):
        """Iniciar transferencia en un hilo separado"""
        thread = threading.Thread(
            target=self._process_transfer,
            args=(transfer_job_id,)
        )
        thread.daemon = True
        thread.start()
    
    def _process_transfer(self, transfer_job_id):
        """
        Procesar transferencia - integra tu lógica de PaYoutubeMusic.py
        """
        try:
            job = TransferJob.objects.get(id=transfer_job_id)
            job.start_processing()
            
            if not self.ytmusic:
                raise Exception("YouTube Music API no está disponible")
            
            # Crear playlist en YouTube Music (tu lógica original)
            youtube_playlist_id = self.ytmusic.create_playlist(
                job.youtube_playlist_name, 
                f"Importada desde Spotify - {job.playlist.name}"
            )
            
            job.youtube_playlist_id = youtube_playlist_id
            job.save()
            
            # Obtener canciones de la playlist
            playlist_songs = PlaylistSong.objects.filter(
                playlist=job.playlist
            ).order_by('position').select_related('song')
            
            # Procesar cada canción (tu lógica original adaptada)
            for playlist_song in playlist_songs:
                self._transfer_song(job, playlist_song.song, youtube_playlist_id)
                
                # Actualizar progreso
                job.processed_songs += 1
                job.save()
            
            job.complete_processing()
            logger.info(f"Transferencia completada: {job.id}")
            
        except Exception as e:
            logger.error(f"Error en transferencia {transfer_job_id}: {e}")
            try:
                job = TransferJob.objects.get(id=transfer_job_id)
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = timezone.now()
                job.save()
            except:
                pass
    
    def _transfer_song(self, job: TransferJob, song: Song, youtube_playlist_id: str):
        """
        Transferir una canción individual - tu lógica de PaYoutubeMusic.py
        """
        # Crear registro del resultado
        result = SongTransferResult.objects.create(
            transfer_job=job,
            song=song,
            search_query=f"{song.title} {song.artist}",
            status=SongTransferResult.FAILED  # Por defecto failed, cambiar si exitoso
        )
        
        try:
            # Tu lógica original de búsqueda
            titulo = song.title
            artista = song.artist
            consulta_busqueda = f"{titulo} {artista}"
            
            # Buscar en YouTube Music
            resultados_busqueda = self.ytmusic.search(consulta_busqueda, filter="songs")
            
            if not resultados_busqueda:
                result.status = SongTransferResult.NOT_FOUND
                result.error_message = "No se encontraron resultados en YouTube Music"
                result.save()
                job.failed_transfers += 1
                job.save()
                return
            
            # Tu lógica de selección del mejor resultado
            id_video_seleccionado = None
            
            # Buscar coincidencia exacta en el título
            for search_result in resultados_busqueda:
                result_title = search_result.get('title', '').lower()
                if titulo.lower() in result_title:
                    id_video_seleccionado = search_result['videoId']
                    break
            
            # Si no hay coincidencia exacta, tomar el primer resultado
            if not id_video_seleccionado:
                id_video_seleccionado = resultados_busqueda[0]['videoId']
            
            # Agregar a la playlist de YouTube Music
            try:
                self.ytmusic.add_playlist_items(youtube_playlist_id, [id_video_seleccionado])
                
                # Éxito
                result.status = SongTransferResult.SUCCESS
                result.youtube_video_id = id_video_seleccionado
                result.save()
                
                # Actualizar también el modelo Song
                song.youtube_video_id = id_video_seleccionado
                song.save()
                
                job.successful_transfers += 1
                job.save()
                
                logger.info(f"Canción transferida: {titulo} - {artista}")
                
            except Exception as error:
                # Tu lógica de manejo de errores HTTP 409 (duplicados)
                if "HTTP 409" in str(error):
                    result.status = SongTransferResult.DUPLICATE
                    result.error_message = "Canción duplicada en la playlist"
                    result.save()
                    
                    # Los duplicados no se cuentan como fallos
                    logger.info(f"Duplicado ignorado: {titulo} - {artista}")
                else:
                    result.status = SongTransferResult.FAILED
                    result.error_message = str(error)
                    result.save()
                    
                    job.failed_transfers += 1
                    job.save()
                    
                    logger.error(f"Error agregando canción: {titulo} - {artista}: {error}")
                    
        except Exception as e:
            result.status = SongTransferResult.FAILED
            result.error_message = str(e)
            result.save()
            
            job.failed_transfers += 1
            job.save()
            
            logger.error(f"Error procesando canción {song.title}: {e}")
    
    def get_youtube_playlist_url(self, playlist_id: str) -> Optional[str]:
        """Obtener URL de la playlist de YouTube Music"""
        if playlist_id:
            return f"https://music.youtube.com/playlist?list={playlist_id}"
        return None
