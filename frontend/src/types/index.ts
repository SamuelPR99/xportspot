// Tipos para el usuario
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

// Tipos para el perfil extendido con Spotify
export interface UserProfile extends User {
  spotify_user_id?: string;
  profile_image?: string;
  country?: string;
  spotify_premium: boolean;
  auto_import_playlists: boolean;
  email_notifications: boolean;
  spotify_connected_at?: string;
  last_spotify_sync?: string;
  has_spotify_connected: boolean;
  has_youtube_music_configured: boolean;
  youtube_music_configured_at?: string;
  display_name: string;
}

// Tipos para las canciones
export interface Song {
  id: number;
  name: string;
  title: string; // Alias para compatibilidad
  artist: string;
  album: string;
  spotify_id: string;
  youtube_video_id: string;
  duration_ms: number | null;
  preview_url?: string;
  spotify_url?: string;
}

// Tipos para las relaciones playlist-canción
export interface PlaylistSong {
  id: number;
  song: Song;
  position: number;
  added_at: string;
}

// Tipos para las playlists
export interface Playlist {
  id: number;
  spotify_id: string;
  youtube_playlist_id?: string;
  name: string;
  description: string;
  total_tracks: number;
  created_at: string;
  updated_at: string;
  user: User;
  songs?: PlaylistSong[];
  spotify_url: string;
  youtube_url?: string;
}

// Tipos para los resultados de transferencia de canciones
export interface SongTransferResult {
  id: number;
  song: Song;
  transfer_status: 'success' | 'failed' | 'not_found';
  youtube_video_id: string;
  youtube_title?: string;
  youtube_artist?: string;
  match_confidence: number;
  error_message: string;
  processed_at: string;
}

// Tipos para los trabajos de transferencia
export interface TransferJob {
  id: number;
  user: User;
  playlist: Playlist;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'partial';
  youtube_playlist_id: string;
  youtube_playlist_name: string;
  total_songs: number;
  processed_songs: number;
  successful_transfers: number;
  failed_transfers: number;
  progress_percentage: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string;
  notes: string;
  song_results?: SongTransferResult[];
}

// Tipos para crear una transferencia
export interface TransferJobCreate {
  playlist_id: number;
  youtube_playlist_name: string;
}

// Tipos para importar playlists
export interface PlaylistImport {
  spotify_playlist_id: string;
  name?: string;
  description?: string;
}

// Tipos para autenticación
export interface AuthResponse {
  success?: boolean;
  token?: string;
  user?: User;
  error?: string;
  data?: any;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

// Tipos para el progreso de transferencia
export interface TransferProgress {
  id: number;
  status: string;
  progress_percentage: number;
  processed_songs: number;
  total_songs: number;
  successful_transfers: number;
  failed_transfers: number;
  youtube_playlist_id: string;
}

// Tipos para YouTube Music
export interface YouTubeMusicStatus {
  is_configured: boolean;
  configured_at?: string;
}

export interface YouTubeMusicGuide {
  title: string;
  description: string;
  steps: {
    step: number;
    title: string;
    description: string;
  }[];
  troubleshooting: {
    problem: string;
    solution: string;
  }[];
}

export interface YouTubeMusicConfig {
  browser_data: string | object;
}
