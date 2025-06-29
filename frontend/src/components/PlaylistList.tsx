import { useState } from 'react';
import type { Playlist } from '../types';

interface PlaylistListProps {
  playlists: Playlist[];
  onStartTransfer: (playlist: Playlist) => void;
  onImportPlaylist: (spotifyUrl: string) => void;
  onRefresh: () => void;
}

const PlaylistList: React.FC<PlaylistListProps> = ({
  playlists,
  onStartTransfer,
  onImportPlaylist,
  onRefresh
}) => {
  const [spotifyUrl, setSpotifyUrl] = useState('');
  const [importing, setImporting] = useState(false);

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!spotifyUrl.trim()) return;

    setImporting(true);
    try {
      await onImportPlaylist(spotifyUrl);
      setSpotifyUrl('');
    } catch (error) {
      console.error('Error importing:', error);
    } finally {
      setImporting(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-6">
      {/* Import Section */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          📥 Importar Playlist desde Spotify
        </h3>
        <form onSubmit={handleImport} className="flex gap-3">
          <div className="flex-1">
            <input
              type="url"
              value={spotifyUrl}
              onChange={(e) => setSpotifyUrl(e.target.value)}
              placeholder="https://open.spotify.com/playlist/..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          <button
            type="submit"
            disabled={importing}
            className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {importing ? 'Importando...' : 'Importar'}
          </button>
        </form>
        <p className="text-sm text-gray-500 mt-2">
          Pega la URL de una playlist pública de Spotify para importarla
        </p>
      </div>

      {/* Playlists Grid */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">
          Tus Playlists ({playlists.length})
        </h3>
        <button
          onClick={onRefresh}
          className="px-4 py-2 text-blue-600 hover:text-blue-800 font-medium"
        >
          🔄 Actualizar
        </button>
      </div>

      {playlists.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <div className="text-gray-400 text-6xl mb-4">🎵</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No tienes playlists aún
          </h3>
          <p className="text-gray-500 mb-6">
            Importa tu primera playlist desde Spotify usando el formulario de arriba
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {playlists.map((playlist) => (
            <div
              key={playlist.id}
              className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-gray-900 mb-1">
                      {playlist.name}
                    </h4>
                    {playlist.description && (
                      <p className="text-gray-600 text-sm mb-2">
                        {playlist.description}
                      </p>
                    )}
                    <div className="flex items-center text-sm text-gray-500 space-x-4">
                      <span>🎵 {playlist.total_tracks} canciones</span>
                      <span>📅 {formatDate(playlist.created_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={() => onStartTransfer(playlist)}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-medium"
                  >
                    🚀 Transferir a YouTube
                  </button>
                  <a
                    href={`https://open.spotify.com/playlist/${playlist.spotify_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    title="Ver en Spotify"
                  >
                    <span className="text-green-600">🎵</span>
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PlaylistList;
