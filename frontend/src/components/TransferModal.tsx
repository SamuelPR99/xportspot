import { useState } from 'react';
import { transferService } from '../services';
import type { Playlist } from '../types';

interface TransferModalProps {
  playlist: Playlist;
  onClose: () => void;
  onComplete: () => void;
}

const TransferModal: React.FC<TransferModalProps> = ({
  playlist,
  onClose,
  onComplete
}) => {
  const [youtubePlaylistName, setYoutubePlaylistName] = useState(playlist.name);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubePlaylistName.trim()) return;

    setIsStarting(true);
    setError('');

    try {
      await transferService.startTransfer({
        playlist_id: playlist.id,
        youtube_playlist_name: youtubePlaylistName.trim()
      });
      
      onComplete();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al iniciar la transferencia');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900">
            🚀 Transferir Playlist
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <div className="mb-6">
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <h4 className="font-medium text-gray-900 mb-2">
              📂 {playlist.name}
            </h4>
            <div className="text-sm text-gray-600 space-y-1">
              <div>🎵 {playlist.total_tracks} canciones</div>
              {playlist.description && (
                <div>📝 {playlist.description}</div>
              )}
            </div>
          </div>
          
          <div className="text-sm text-gray-600">
            Esta playlist se transferirá a YouTube Music. El proceso puede tomar varios minutos.
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label htmlFor="playlistName" className="block text-sm font-medium text-gray-700 mb-2">
              Nombre de la playlist en YouTube Music
            </label>
            <input
              id="playlistName"
              type="text"
              value={youtubePlaylistName}
              onChange={(e) => setYoutubePlaylistName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Nombre para la nueva playlist"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Se creará una nueva playlist con este nombre en YouTube Music
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isStarting || !youtubePlaylistName.trim()}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStarting ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Iniciando...
                </div>
              ) : (
                'Iniciar Transferencia'
              )}
            </button>
          </div>
        </form>

        <div className="mt-4 text-xs text-gray-500">
          💡 <strong>Tip:</strong> Asegúrate de que tu archivo browser.json de YouTube Music esté configurado correctamente en el servidor.
        </div>
      </div>
    </div>
  );
};

export default TransferModal;
