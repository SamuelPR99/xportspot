import axios from 'axios';
import type { 
  UserProfile, 
  Playlist, 
  TransferJob, 
  TransferJobCreate, 
  PlaylistImport, 
  LoginCredentials,
  AuthResponse,
  TransferProgress,
  YouTubeMusicStatus,
  YouTubeMusicGuide,
  YouTubeMusicConfig
} from '../types';

// Configurar axios para la API
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para manejar tokens de autenticación
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de respuesta
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================
// API METHODS
// ============================================

// Autenticación
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post('/auth/login/', credentials);
    return response.data;
  },

  register: async (userData: any): Promise<AuthResponse> => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout/');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  },

  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  updateProfile: async (data: Partial<UserProfile>): Promise<UserProfile> => {
    const response = await api.put('/auth/profile/', data);
    return response.data;
  }
};

// Spotify Integration
export const spotifyAPI = {
  getAuthUrl: async (): Promise<{ auth_url: string }> => {
    const response = await api.get('/auth/spotify/');
    return response.data;
  },

  handleCallback: async (code: string): Promise<AuthResponse> => {
    const response = await api.post('/auth/spotify/callback/', { code });
    return response.data;
  },

  disconnect: async (): Promise<void> => {
    await api.post('/auth/spotify/disconnect/');
  },

  getPlaylists: async (): Promise<any[]> => {
    const response = await api.get('/auth/spotify/playlists/');
    return response.data;
  }
};

// Playlists
export const playlistAPI = {
  getAll: async (): Promise<Playlist[]> => {
    const response = await api.get('/playlists/');
    return response.data;
  },

  getById: async (id: number): Promise<Playlist> => {
    const response = await api.get(`/playlists/${id}/`);
    return response.data;
  },

  importFromSpotify: async (data: PlaylistImport): Promise<Playlist> => {
    const response = await api.post('/playlists/import_from_spotify/', data);
    return response.data;
  },

  exportToCsv: async (id: number): Promise<Blob> => {
    const response = await api.get(`/playlists/${id}/export_csv/`, {
      responseType: 'blob'
    });
    return response.data;
  },

  debugSongs: async (id: number): Promise<any> => {
    const response = await api.get(`/playlists/${id}/debug_songs/`);
    return response.data;
  },

  getUrls: async (id: number): Promise<{ spotify_url: string; youtube_url?: string }> => {
    const response = await api.get(`/playlists/${id}/playlist_url/`);
    return response.data;
  },

  getSongs: async (id: number): Promise<any[]> => {
    const response = await api.get(`/playlists/${id}/songs/`);
    return response.data;
  }
};

// Transfer Jobs
export const transferAPI = {
  getAll: async (): Promise<TransferJob[]> => {
    const response = await api.get('/transfer-jobs/');
    return response.data;
  },

  getById: async (id: number): Promise<TransferJob> => {
    const response = await api.get(`/transfer-jobs/${id}/`);
    return response.data;
  },

  startTransfer: async (data: TransferJobCreate): Promise<TransferJob> => {
    const response = await api.post('/transfer-jobs/start_transfer/', data);
    return response.data;
  },

  cancelTransfer: async (id: number): Promise<TransferJob> => {
    const response = await api.post(`/transfer-jobs/${id}/cancel_transfer/`);
    return response.data;
  },

  getProgress: async (id: number): Promise<TransferProgress> => {
    const response = await api.get(`/transfer-jobs/${id}/progress/`);
    return response.data;
  }
};

// YouTube Music Configuration
export const youtubeMusicAPI = {
  getStatus: async (): Promise<YouTubeMusicStatus> => {
    const response = await api.get('/auth/youtube-music/status/');
    return response.data;
  },

  configure: async (data: YouTubeMusicConfig): Promise<AuthResponse> => {
    const response = await api.post('/auth/youtube-music/configure/', data);
    return response.data;
  },

  disconnect: async (): Promise<void> => {
    await api.post('/auth/youtube-music/disconnect/');
  },

  getSetupGuide: async (): Promise<YouTubeMusicGuide> => {
    const response = await api.get('/auth/youtube-music/setup-guide/');
    return response.data;
  },

  testConnection: async (): Promise<any> => {
    const response = await api.post('/auth/youtube-music/test-connection/');
    return response.data;
  }
};

// Utilidades
export const utils = {
  extractSpotifyPlaylistId: (url: string): string | null => {
    const regex = /spotify\.com\/playlist\/([a-zA-Z0-9]+)/;
    const match = url.match(regex);
    return match ? match[1] : null;
  },

  formatDuration: (ms: number | null): string => {
    if (!ms) return '0:00';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  },

  formatDate: (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
};

export default api;
