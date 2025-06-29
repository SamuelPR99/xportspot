import { useState, useEffect } from 'react';
import { playlistService, transferService } from '../services';
import type { Playlist, TransferJob } from '../types';
import PlaylistList from './PlaylistList';
import TransferHistory from './TransferHistory';
import TransferModal from './TransferModal';

interface DashboardProps {
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [activeTab, setActiveTab] = useState<'playlists' | 'transfers'>('playlists');
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [transferJobs, setTransferJobs] = useState<TransferJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [selectedPlaylist, setSelectedPlaylist] = useState<Playlist | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [playlistsData, transfersData] = await Promise.all([
        playlistService.getPlaylists(),
        transferService.getTransferJobs()
      ]);
      setPlaylists(playlistsData);
      setTransferJobs(transfersData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTransfer = (playlist: Playlist) => {
    setSelectedPlaylist(playlist);
    setShowTransferModal(true);
  };

  const handleTransferComplete = () => {
    setShowTransferModal(false);
    setSelectedPlaylist(null);
    loadData(); // Recargar datos
  };

  const handleImportPlaylist = async (spotifyUrl: string) => {
    try {
      // Extraer ID de la URL de Spotify
      const playlistId = spotifyUrl.split('/playlist/')[1]?.split('?')[0];
      if (!playlistId) {
        throw new Error('URL de Spotify inválida');
      }

      await playlistService.importFromSpotify({
        spotify_playlist_id: playlistId
      });
      
      loadData(); // Recargar las playlists
    } catch (error) {
      console.error('Error importing playlist:', error);
      alert('Error al importar la playlist');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                🎵 XportSpot
              </h1>
            </div>
            <button
              onClick={onLogout}
              className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              Cerrar Sesión
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('playlists')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'playlists'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📂 Mis Playlists ({playlists.length})
            </button>
            <button
              onClick={() => setActiveTab('transfers')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'transfers'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🔄 Historial de Transferencias ({transferJobs.length})
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="mt-8">
          {activeTab === 'playlists' ? (
            <PlaylistList
              playlists={playlists}
              onStartTransfer={handleStartTransfer}
              onImportPlaylist={handleImportPlaylist}
              onRefresh={loadData}
            />
          ) : (
            <TransferHistory
              transferJobs={transferJobs}
              onRefresh={loadData}
            />
          )}
        </div>
      </div>

      {/* Transfer Modal */}
      {showTransferModal && selectedPlaylist && (
        <TransferModal
          playlist={selectedPlaylist}
          onClose={() => setShowTransferModal(false)}
          onComplete={handleTransferComplete}
        />
      )}
    </div>
  );
};

export default Dashboard;
