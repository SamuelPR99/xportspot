import api from './api';
import type { 
  Playlist, 
  TransferJob, 
  TransferJobCreate, 
  TransferProgress,
  PlaylistImport,
  Song,
  AuthResponse,
  LoginCredentials
} from '../types';

// Servicio de autenticación
export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post('/auth/token/', credentials);
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('auth_token');
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('auth_token');
  },

  getToken: (): string | null => {
    return localStorage.getItem('auth_token');
  },

  setToken: (token: string) => {
    localStorage.setItem('auth_token', token);
  }
};

// Servicio de playlists
export const playlistService = {
  // Obtener todas las playlists del usuario
  getPlaylists: async (): Promise<Playlist[]> => {
    const response = await api.get('/playlists/');
    return response.data;
  },

  // Obtener una playlist específica
  getPlaylist: async (id: number): Promise<Playlist> => {
    const response = await api.get(`/playlists/${id}/`);
    return response.data;
  },

  // Obtener canciones de una playlist
  getPlaylistSongs: async (id: number): Promise<Song[]> => {
    const response = await api.get(`/playlists/${id}/songs/`);
    return response.data;
  },

  // Importar playlist desde Spotify
  importFromSpotify: async (data: PlaylistImport): Promise<Playlist> => {
    const response = await api.post('/playlists/import_from_spotify/', data);
    return response.data;
  },

  // Crear playlist manualmente
  createPlaylist: async (playlist: Partial<Playlist>): Promise<Playlist> => {
    const response = await api.post('/playlists/', playlist);
    return response.data;
  },

  // Actualizar playlist
  updatePlaylist: async (id: number, playlist: Partial<Playlist>): Promise<Playlist> => {
    const response = await api.put(`/playlists/${id}/`, playlist);
    return response.data;
  },

  // Eliminar playlist
  deletePlaylist: async (id: number): Promise<void> => {
    await api.delete(`/playlists/${id}/`);
  }
};

// Servicio de trabajos de transferencia
export const transferService = {
  // Obtener todos los trabajos de transferencia
  getTransferJobs: async (): Promise<TransferJob[]> => {
    const response = await api.get('/transfer-jobs/');
    return response.data;
  },

  // Obtener un trabajo específico
  getTransferJob: async (id: number): Promise<TransferJob> => {
    const response = await api.get(`/transfer-jobs/${id}/`);
    return response.data;
  },

  // Iniciar nueva transferencia
  startTransfer: async (data: TransferJobCreate): Promise<TransferJob> => {
    const response = await api.post('/transfer-jobs/start_transfer/', data);
    return response.data;
  },

  // Obtener progreso de transferencia
  getTransferProgress: async (id: number): Promise<TransferProgress> => {
    const response = await api.get(`/transfer-jobs/${id}/progress/`);
    return response.data;
  },

  // Cancelar transferencia
  cancelTransfer: async (id: number): Promise<TransferJob> => {
    const response = await api.post(`/transfer-jobs/${id}/cancel_transfer/`);
    return response.data;
  }
};

// Servicio de canciones
export const songService = {
  // Obtener todas las canciones del usuario
  getSongs: async (): Promise<Song[]> => {
    const response = await api.get('/songs/');
    return response.data;
  },

  // Obtener una canción específica
  getSong: async (id: number): Promise<Song> => {
    const response = await api.get(`/songs/${id}/`);
    return response.data;
  }
};

// Utilidades para URLs de YouTube Music
export const youtubeUtils = {
  getPlaylistUrl: (playlistId: string): string => {
    return `https://music.youtube.com/playlist?list=${playlistId}`;
  },

  getVideoUrl: (videoId: string): string => {
    return `https://music.youtube.com/watch?v=${videoId}`;
  }
};
