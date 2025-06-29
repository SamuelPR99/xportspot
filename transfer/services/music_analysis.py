"""
Servicio para análisis musical multiplataforma
"""

from datetime import datetime, timedelta
from django.utils import timezone
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class MusicAnalysisService:
    """Servicio para análisis de datos musicales unificados"""
    
    def __init__(self, user):
        self.user = user
    
    def get_user_connections(self):
        """Obtiene todas las conexiones activas del usuario"""
        return self.user.music_connections.filter(is_active=True)
    
    def get_unified_stats(self, period='monthly'):
        """Obtiene estadísticas unificadas de todas las plataformas"""
        connections = self.get_user_connections()
        
        unified_stats = {
            'total_minutes': 0,
            'total_tracks': 0,
            'platforms_connected': len(connections),
            'top_artists': [],
            'top_genres': [],
            'top_tracks': [],
            'listening_patterns': {},
            'platform_breakdown': []
        }
        
        # Agregar datos de cada plataforma
        for connection in connections:
            platform_stats = self._get_platform_stats(connection, period)
            if platform_stats:
                unified_stats['total_minutes'] += platform_stats.get('total_minutes', 0)
                unified_stats['total_tracks'] += platform_stats.get('total_tracks', 0)
                
                # Agregar breakdown por plataforma
                unified_stats['platform_breakdown'].append({
                    'platform': connection.platform.display_name,
                    'color': connection.platform.color,
                    'minutes': platform_stats.get('total_minutes', 0),
                    'tracks': platform_stats.get('total_tracks', 0),
                    'percentage': 0  # Se calculará después
                })
        
        # Calcular porcentajes
        if unified_stats['total_minutes'] > 0:
            for platform in unified_stats['platform_breakdown']:
                platform['percentage'] = round(
                    (platform['minutes'] / unified_stats['total_minutes']) * 100, 1
                )
        
        # Combinar y rankear artistas, géneros y tracks
        unified_stats.update(self._combine_top_data(connections, period))
        
        return unified_stats
    
    def _get_platform_stats(self, connection, period):
        """Obtiene estadísticas de una plataforma específica"""
        try:
            # Buscar estadísticas existentes
            stats = connection.user.listening_stats.filter(
                platform_connection=connection,
                period_type=period
            ).first()
            
            if stats:
                return {
                    'total_minutes': stats.total_minutes,
                    'total_tracks': stats.total_tracks,
                    'unique_artists': stats.unique_artists,
                    'top_artists': stats.top_artists,
                    'top_genres': stats.top_genres,
                    'top_tracks': stats.top_tracks
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting platform stats for {connection.platform.name}: {e}")
            return None
    
    def _combine_top_data(self, connections, period):
        """Combina y rankea datos de todas las plataformas"""
        all_artists = Counter()
        all_genres = Counter()
        all_tracks = Counter()
        
        for connection in connections:
            try:
                stats = connection.user.listening_stats.filter(
                    platform_connection=connection,
                    period_type=period
                ).first()
                
                if not stats:
                    continue
                
                # Combinar artistas
                for artist_data in stats.top_artists:
                    artist_name = artist_data.get('name')
                    minutes = artist_data.get('minutes', 0)
                    if artist_name:
                        all_artists[artist_name] += minutes
                
                # Combinar géneros
                for genre_data in stats.top_genres:
                    genre_name = genre_data.get('name')
                    minutes = genre_data.get('minutes', 0)
                    if genre_name:
                        all_genres[genre_name] += minutes
                
                # Combinar tracks
                for track_data in stats.top_tracks:
                    track_key = f"{track_data.get('name')} - {track_data.get('artist')}"
                    minutes = track_data.get('minutes', 0)
                    if track_key:
                        all_tracks[track_key] += minutes
                        
            except Exception as e:
                logger.error(f"Error combining data from {connection.platform.name}: {e}")
                continue
        
        return {
            'top_artists': [
                {'name': name, 'minutes': minutes, 'rank': i+1}
                for i, (name, minutes) in enumerate(all_artists.most_common(20))
            ],
            'top_genres': [
                {'name': name, 'minutes': minutes, 'rank': i+1}
                for i, (name, minutes) in enumerate(all_genres.most_common(15))
            ],
            'top_tracks': [
                {'track': name, 'minutes': minutes, 'rank': i+1}
                for i, (name, minutes) in enumerate(all_tracks.most_common(50))
            ]
        }
    
    def calculate_music_compatibility(self, other_user):
        """Calcula compatibilidad musical entre dos usuarios"""
        try:
            # Obtener estadísticas de ambos usuarios
            user1_stats = self.get_unified_stats()
            user2_stats = MusicAnalysisService(other_user).get_unified_stats()
            
            # Calcular compatibilidad de artistas
            artist_compatibility = self._calculate_artist_compatibility(
                user1_stats['top_artists'], 
                user2_stats['top_artists']
            )
            
            # Calcular compatibilidad de géneros
            genre_compatibility = self._calculate_genre_compatibility(
                user1_stats['top_genres'], 
                user2_stats['top_genres']
            )
            
            # Compatibilidad general (promedio ponderado)
            overall_compatibility = (artist_compatibility * 0.6) + (genre_compatibility * 0.4)
            
            # Encontrar artistas y géneros compartidos
            shared_artists = self._find_shared_items(
                user1_stats['top_artists'], 
                user2_stats['top_artists'], 
                'name'
            )
            
            shared_genres = self._find_shared_items(
                user1_stats['top_genres'], 
                user2_stats['top_genres'], 
                'name'
            )
            
            return {
                'overall_compatibility': round(overall_compatibility, 1),
                'artist_compatibility': round(artist_compatibility, 1),
                'genre_compatibility': round(genre_compatibility, 1),
                'shared_artists': shared_artists[:10],  # Top 10 compartidos
                'shared_genres': shared_genres[:10],
                'compatibility_level': self._get_compatibility_level(overall_compatibility)
            }
            
        except Exception as e:
            logger.error(f"Error calculating music compatibility: {e}")
            return None
    
    def _calculate_artist_compatibility(self, artists1, artists2):
        """Calcula compatibilidad basada en artistas"""
        if not artists1 or not artists2:
            return 0.0
        
        # Crear sets de artistas para cada usuario
        set1 = {artist['name'].lower() for artist in artists1}
        set2 = {artist['name'].lower() for artist in artists2}
        
        # Calcular intersección y unión
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        # Índice de Jaccard modificado (0-100)
        jaccard_index = intersection / union
        return jaccard_index * 100
    
    def _calculate_genre_compatibility(self, genres1, genres2):
        """Calcula compatibilidad basada en géneros"""
        if not genres1 or not genres2:
            return 0.0
        
        # Crear sets de géneros
        set1 = {genre['name'].lower() for genre in genres1}
        set2 = {genre['name'].lower() for genre in genres2}
        
        # Calcular intersección y unión
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        # Índice de Jaccard (0-100)
        jaccard_index = intersection / union
        return jaccard_index * 100
    
    def _find_shared_items(self, list1, list2, key):
        """Encuentra elementos compartidos entre dos listas"""
        items1 = {item[key].lower(): item for item in list1}
        items2 = {item[key].lower(): item for item in list2}
        
        shared = []
        for name in items1.keys():
            if name in items2:
                shared.append({
                    'name': items1[name][key],
                    'user1_minutes': items1[name].get('minutes', 0),
                    'user2_minutes': items2[name].get('minutes', 0)
                })
        
        # Ordenar por minutos combinados
        shared.sort(key=lambda x: x['user1_minutes'] + x['user2_minutes'], reverse=True)
        return shared
    
    def _get_compatibility_level(self, score):
        """Determina el nivel de compatibilidad basado en el puntaje"""
        if score >= 80:
            return {'level': 'Gemelos Musicales', 'emoji': '🎭', 'color': '#FF6B6B'}
        elif score >= 65:
            return {'level': 'Muy Compatible', 'emoji': '🎵', 'color': '#4ECDC4'}
        elif score >= 50:
            return {'level': 'Compatible', 'emoji': '🎶', 'color': '#45B7D1'}
        elif score >= 35:
            return {'level': 'Algo en Común', 'emoji': '🎸', 'color': '#F9CA24'}
        elif score >= 20:
            return {'level': 'Diferente Onda', 'emoji': '🎤', 'color': '#E17055'}
        else:
            return {'level': 'Mundos Aparte', 'emoji': '🌍', 'color': '#636E72'}
    
    def get_music_recommendations(self, limit=20):
        """Genera recomendaciones musicales basadas en amigos con gustos similares"""
        try:
            # Obtener amigos con alta compatibilidad
            compatible_friends = []
            
            # Obtener amistades aceptadas
            friendships = self.user.sent_friend_requests.filter(status='accepted').union(
                self.user.received_friend_requests.filter(status='accepted')
            )
            
            for friendship in friendships:
                friend = friendship.addressee if friendship.requester == self.user else friendship.requester
                
                # Obtener o calcular compatibilidad
                compatibility = self._get_or_calculate_compatibility(friend)
                if compatibility and compatibility['overall_compatibility'] >= 40:
                    compatible_friends.append({
                        'friend': friend,
                        'compatibility': compatibility
                    })
            
            # Ordenar por compatibilidad
            compatible_friends.sort(key=lambda x: x['compatibility']['overall_compatibility'], reverse=True)
            
            # Generar recomendaciones basadas en amigos compatibles
            recommendations = []
            user_artists = set(artist['name'].lower() for artist in self.get_unified_stats()['top_artists'])
            
            for friend_data in compatible_friends[:5]:  # Top 5 amigos más compatibles
                friend_stats = MusicAnalysisService(friend_data['friend']).get_unified_stats()
                
                for artist in friend_stats['top_artists'][:10]:  # Top 10 del amigo
                    if artist['name'].lower() not in user_artists:
                        recommendations.append({
                            'artist_name': artist['name'],
                            'minutes': artist['minutes'],
                            'recommended_by': friend_data['friend'].display_name,
                            'compatibility_score': friend_data['compatibility']['overall_compatibility'],
                            'reason': f"A {friend_data['friend'].display_name} le encanta (compatibilidad: {friend_data['compatibility']['overall_compatibility']}%)"
                        })
            
            # Remover duplicados y limitar
            seen = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec['artist_name'].lower() not in seen:
                    seen.add(rec['artist_name'].lower())
                    unique_recommendations.append(rec)
            
            return unique_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating music recommendations: {e}")
            return []
    
    def _get_or_calculate_compatibility(self, other_user):
        """Obtiene compatibilidad existente o la calcula"""
        from .models import MusicCompatibility
        
        try:
            # Buscar compatibilidad existente (en cualquier dirección)
            compatibility = MusicCompatibility.objects.filter(
                user1=self.user, user2=other_user
            ).first() or MusicCompatibility.objects.filter(
                user1=other_user, user2=self.user
            ).first()
            
            if compatibility:
                return {
                    'overall_compatibility': compatibility.overall_compatibility,
                    'artist_compatibility': compatibility.artist_compatibility,
                    'genre_compatibility': compatibility.genre_compatibility,
                    'shared_artists': compatibility.shared_artists,
                    'shared_genres': compatibility.shared_genres
                }
            
            # Si no existe, calcular nueva compatibilidad
            return self.calculate_music_compatibility(other_user)
            
        except Exception as e:
            logger.error(f"Error getting/calculating compatibility: {e}")
            return None
