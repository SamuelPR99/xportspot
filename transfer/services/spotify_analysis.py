"""
Servicio de análisis musical de Spotify para la red social
"""
import requests
import json
import base64
import logging
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class SpotifyMusicAnalysisService:
    """Servicio para análisis musical detallado de Spotify"""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://api.spotify.com/v1'
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_user_profile(self):
        """Obtiene perfil del usuario de Spotify"""
        try:
            response = requests.get(f"{self.base_url}/me", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def get_top_artists(self, time_range='medium_term', limit=50):
        """
        Obtiene artistas más escuchados
        time_range: short_term (4 weeks), medium_term (6 months), long_term (years)
        """
        try:
            response = requests.get(
                f"{self.base_url}/me/top/artists",
                headers=self.headers,
                params={'time_range': time_range, 'limit': limit}
            )
            
            if response.status_code == 200:
                data = response.json()
                artists = []
                
                for artist in data.get('items', []):
                    artists.append({
                        'name': artist['name'],
                        'spotify_id': artist['id'],
                        'genres': artist.get('genres', []),
                        'popularity': artist.get('popularity', 0),
                        'followers': artist.get('followers', {}).get('total', 0),
                        'image_url': artist.get('images', [{}])[0].get('url') if artist.get('images') else None,
                        'external_url': artist.get('external_urls', {}).get('spotify')
                    })
                
                return artists
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting top artists: {e}")
            return []
    
    def get_top_tracks(self, time_range='medium_term', limit=50):
        """Obtiene canciones más escuchadas"""
        try:
            response = requests.get(
                f"{self.base_url}/me/top/tracks",
                headers=self.headers,
                params={'time_range': time_range, 'limit': limit}
            )
            
            if response.status_code == 200:
                data = response.json()
                tracks = []
                
                for track in data.get('items', []):
                    tracks.append({
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'spotify_id': track['id'],
                        'duration_ms': track.get('duration_ms', 0),
                        'popularity': track.get('popularity', 0),
                        'preview_url': track.get('preview_url'),
                        'external_url': track.get('external_urls', {}).get('spotify'),
                        'image_url': track['album'].get('images', [{}])[0].get('url') if track['album'].get('images') else None
                    })
                
                return tracks
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting top tracks: {e}")
            return []
    
    def get_recently_played(self, limit=50):
        """Obtiene canciones reproducidas recientemente"""
        try:
            response = requests.get(
                f"{self.base_url}/me/player/recently-played",
                headers=self.headers,
                params={'limit': limit}
            )
            
            if response.status_code == 200:
                data = response.json()
                tracks = []
                
                for item in data.get('items', []):
                    track = item['track']
                    tracks.append({
                        'name': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'album': track['album']['name'],
                        'played_at': item['played_at'],
                        'spotify_id': track['id'],
                        'duration_ms': track.get('duration_ms', 0),
                        'external_url': track.get('external_urls', {}).get('spotify')
                    })
                
                return tracks
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting recently played: {e}")
            return []
    
    def get_audio_features(self, track_ids):
        """Obtiene características de audio para múltiples tracks"""
        try:
            if not track_ids:
                return []
            
            # Spotify API permite hasta 100 IDs por request
            chunks = [track_ids[i:i+100] for i in range(0, len(track_ids), 100)]
            all_features = []
            
            for chunk in chunks:
                response = requests.get(
                    f"{self.base_url}/audio-features",
                    headers=self.headers,
                    params={'ids': ','.join(chunk)}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    all_features.extend(data.get('audio_features', []))
            
            return all_features
            
        except Exception as e:
            logger.error(f"Error getting audio features: {e}")
            return []
    
    def analyze_listening_patterns(self, time_range='medium_term'):
        """Analiza patrones de escucha del usuario"""
        try:
            # Obtener datos de canciones y artistas top
            top_artists = self.get_top_artists(time_range)
            top_tracks = self.get_top_tracks(time_range)
            recently_played = self.get_recently_played()
            
            # Extraer géneros
            all_genres = []
            for artist in top_artists:
                all_genres.extend(artist.get('genres', []))
            
            # Contar géneros
            genre_counts = Counter(all_genres)
            
            # Obtener características de audio de top tracks
            track_ids = [track['spotify_id'] for track in top_tracks if track.get('spotify_id')]
            audio_features = self.get_audio_features(track_ids)
            
            # Calcular promedios de características musicales
            audio_averages = self._calculate_audio_averages(audio_features)
            
            # Calcular estadísticas de tiempo de escucha
            listening_stats = self._calculate_listening_stats(recently_played, top_tracks)
            
            return {
                'period': time_range,
                'top_artists': top_artists[:20],
                'top_tracks': top_tracks[:50],
                'top_genres': [
                    {'name': genre, 'count': count, 'percentage': round((count / len(all_genres)) * 100, 1)}
                    for genre, count in genre_counts.most_common(15)
                ] if all_genres else [],
                'audio_profile': audio_averages,
                'listening_stats': listening_stats,
                'total_artists': len(top_artists),
                'total_unique_genres': len(genre_counts),
                'diversity_score': self._calculate_diversity_score(genre_counts, top_artists)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing listening patterns: {e}")
            return None
    
    def _calculate_audio_averages(self, audio_features):
        """Calcula promedios de características de audio"""
        if not audio_features:
            return {}
        
        # Filtrar features válidos (no None)
        valid_features = [f for f in audio_features if f is not None]
        if not valid_features:
            return {}
        
        features_to_average = [
            'danceability', 'energy', 'speechiness', 'acousticness',
            'instrumentalness', 'liveness', 'valence', 'tempo'
        ]
        
        averages = {}
        for feature in features_to_average:
            values = [f.get(feature, 0) for f in valid_features if f.get(feature) is not None]
            if values:
                averages[feature] = round(sum(values) / len(values), 3)
        
        return averages
    
    def _calculate_listening_stats(self, recently_played, top_tracks):
        """Calcula estadísticas de escucha"""
        try:
            # Calcular minutos totales aproximados (basado en top tracks)
            total_duration_ms = sum(track.get('duration_ms', 0) for track in top_tracks)
            estimated_total_minutes = (total_duration_ms * 2) // 60000  # Estimación x2 para todo el período
            
            # Analizar patrones horarios de recently_played
            hour_patterns = {}
            if recently_played:
                hour_counts = defaultdict(int)
                
                for track in recently_played:
                    try:
                        played_at = datetime.fromisoformat(track['played_at'].replace('Z', '+00:00'))
                        hour = played_at.hour
                        hour_counts[hour] += 1
                    except:
                        continue
                
                hour_patterns = dict(hour_counts)
            
            return {
                'estimated_total_minutes': estimated_total_minutes,
                'estimated_total_hours': round(estimated_total_minutes / 60, 1),
                'average_track_duration': round(total_duration_ms / len(top_tracks) / 1000 / 60, 1) if top_tracks else 0,
                'hourly_patterns': hour_patterns,
                'most_active_hour': max(hour_patterns.items(), key=lambda x: x[1])[0] if hour_patterns else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating listening stats: {e}")
            return {}
    
    def _calculate_diversity_score(self, genre_counts, top_artists):
        """Calcula un puntaje de diversidad musical (0-100)"""
        try:
            if not genre_counts or not top_artists:
                return 0
            
            # Diversidad de géneros usando Índice de Shannon simplificado
            total_genres = sum(genre_counts.values())
            if total_genres == 0:
                return 0
            
            # Calcular entropía
            entropy = 0
            for count in genre_counts.values():
                if count > 0:
                    p = count / total_genres
                    entropy -= p * (p * 100 // 100)  # Simplificado sin log
            
            # Normalizar a 0-100
            max_entropy = len(genre_counts)
            genre_score = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
            
            # Diversidad de popularidad de artistas
            popularities = [artist.get('popularity', 0) for artist in top_artists]
            if not popularities:
                return genre_score
            
            avg_popularity = sum(popularities) / len(popularities)
            popularity_variance = sum((x - avg_popularity)**2 for x in popularities) / len(popularities)
            popularity_score = min(popularity_variance / 25, 100)  # Normalizar
            
            # Puntaje combinado
            diversity_score = (genre_score * 0.7) + (popularity_score * 0.3)
            return round(min(diversity_score, 100), 1)
            
        except Exception as e:
            logger.error(f"Error calculating diversity score: {e}")
            return 0
    
    def create_listening_stats_data(self, user_connection, period_type='monthly'):
        """Crea datos de estadísticas de escucha para almacenar en BD"""
        try:
            # Mapear period_type a time_range de Spotify
            time_range_map = {
                'monthly': 'medium_term',
                'yearly': 'long_term',
                'weekly': 'short_term'
            }
            
            time_range = time_range_map.get(period_type, 'medium_term')
            analysis = self.analyze_listening_patterns(time_range)
            
            if not analysis:
                return None
            
            # Calcular fechas del período
            now = timezone.now().date()
            if period_type == 'monthly':
                period_start = now.replace(day=1)
                period_end = now
            elif period_type == 'yearly':
                period_start = now.replace(month=1, day=1)
                period_end = now
            else:  # weekly
                period_start = now - timedelta(days=7)
                period_end = now
            
            # Formatear top artists para BD
            top_artists = []
            for i, artist in enumerate(analysis['top_artists'][:20]):
                top_artists.append({
                    'name': artist['name'],
                    'minutes': analysis['listening_stats']['estimated_total_minutes'] // (i + 1),  # Distribución estimada
                    'plays': max(100 // (i + 1), 1),  # Estimación de reproducciones
                    'spotify_id': artist.get('spotify_id'),
                    'rank': i + 1
                })
            
            # Formatear top genres para BD
            top_genres = []
            for i, genre in enumerate(analysis['top_genres'][:15]):
                estimated_minutes = int(analysis['listening_stats']['estimated_total_minutes'] * genre['percentage'] / 100)
                top_genres.append({
                    'name': genre['name'],
                    'minutes': estimated_minutes,
                    'percentage': genre['percentage'],
                    'rank': i + 1
                })
            
            # Formatear top tracks para BD
            top_tracks = []
            for i, track in enumerate(analysis['top_tracks'][:50]):
                top_tracks.append({
                    'name': track['name'],
                    'artist': track['artist'],
                    'minutes': max(analysis['listening_stats']['estimated_total_minutes'] // (i + 5), 1),
                    'plays': max(50 // (i + 1), 1),
                    'spotify_id': track.get('spotify_id'),
                    'rank': i + 1
                })
            
            return {
                'period_type': period_type,
                'period_start': period_start,
                'period_end': period_end,
                'total_minutes': analysis['listening_stats']['estimated_total_minutes'],
                'total_tracks': len(analysis['top_tracks']),
                'unique_artists': len(analysis['top_artists']),
                'unique_albums': len(set(track.get('album', '') for track in analysis['top_tracks'])),
                'top_artists': top_artists,
                'top_genres': top_genres,
                'top_tracks': top_tracks,
                'listening_patterns': analysis['listening_stats']['hourly_patterns'],
                'audio_profile': analysis['audio_profile'],
                'diversity_score': analysis['diversity_score']
            }
            
        except Exception as e:
            logger.error(f"Error creating listening stats data: {e}")
            return None
