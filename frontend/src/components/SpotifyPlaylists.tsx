import { useState, useEffect } from 'react';
import { spotifyService } from '../services';

interface SpotifyPlaylist {
  id: string;
  name: string;
  description: string;
  track_count: number;
  public: boolean;
  collaborative: boolean;
  owner: string;
  images: Array<{ url: string; height: number; width: number }>;
}

interface SpotifyPlaylistsProps {
  isConnected: boolean;
  onImportPlaylist: (playlistId: string, name?: string, description?: string) => void;
}

const SpotifyPlaylists: React.FC<SpotifyPlaylistsProps> = ({ isConnected, onImportPlaylist }) => {
  const [playlists, setPlaylists] = useState<SpotifyPlaylist[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importingIds, setImportingIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isConnected) {
      loadSpotifyPlaylists();
    }
  }, [isConnected]);

  const loadSpotifyPlaylists = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await spotifyService.getPlaylists();
      setPlaylists(response.playlists);
    } catch (error: any) {
      setError(error.response?.data?.error || 'Error al cargar playlists de Spotify');
    } finally {
      setLoading(false);
    }
  };

  const handleImportPlaylist = async (playlist: SpotifyPlaylist) => {
    setImportingIds(prev => new Set(prev).add(playlist.id));
    try {
      await onImportPlaylist(playlist.id, playlist.name, playlist.description);
    } catch (error) {
      console.error('Error importing playlist:', error);
    } finally {
      setImportingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(playlist.id);
        return newSet;
      });
    }
  };

  if (!isConnected) {
    return null;
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          🎵 Tus Playlists de Spotify
        </h3>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
          <span className="ml-2 text-gray-600">Cargando playlists...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          🎵 Tus Playlists de Spotify
        </h3>
        <div className="text-center py-8">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadSpotifyPlaylists}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          🎵 Tus Playlists de Spotify ({playlists.length})
        </h3>
        <button
          onClick={loadSpotifyPlaylists}
          className="px-3 py-1 text-sm text-green-600 hover:text-green-800 font-medium"
        >
          🔄 Actualizar
        </button>
      </div>

      {playlists.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-gray-400 text-6xl mb-4">🎵</div>
          <p className="text-gray-500">No se encontraron playlists en tu cuenta de Spotify</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {playlists.map((playlist) => (
            <div
              key={playlist.id}
              className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
            >
              <div className="aspect-square bg-gray-100 flex items-center justify-center">
                {playlist.images.length > 0 ? (
                  <img
                    src={playlist.images[0].url}
                    alt={playlist.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-gray-400 text-4xl">🎵</div>
                )}
              </div>
              
              <div className="p-4">
                <h4 className="font-semibold text-gray-900 mb-1 truncate" title={playlist.name}>
                  {playlist.name}
                </h4>
                
                {playlist.description && (
                  <p className="text-sm text-gray-600 mb-2 line-clamp-2" title={playlist.description}>
                    {playlist.description}
                  </p>
                )}
                
                <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
                  <span>{playlist.track_count} canciones</span>
                  <span>por {playlist.owner}</span>
                </div>
                
                <button
                  onClick={() => handleImportPlaylist(playlist)}
                  disabled={importingIds.has(playlist.id)}
                  className="w-full px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                >
                  {importingIds.has(playlist.id) ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Importando...
                    </div>
                  ) : (
                    '📥 Importar'
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SpotifyPlaylists;
