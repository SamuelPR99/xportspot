import { useState, useEffect } from 'react';
import { playlistAPI, transferAPI, spotifyAPI, utils } from '../services/api';
import type { Playlist, TransferJob } from '../types';
import PlaylistList from './PlaylistList';
import TransferHistory from './TransferHistory';
import TransferModal from './TransferModal';
import SpotifyStatus from './SpotifyStatus';
import YouTubeMusicSetup from './YouTubeMusicSetup';

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
  const [isSpotifyConnected, setIsSpotifyConnected] = useState(false);
  const [spotifyRefreshTrigger, setSpotifyRefreshTrigger] = useState(0);
  const [spotifyPlaylists, setSpotifyPlaylists] = useState<any[]>([]);
  const [loadingSpotifyPlaylists, setLoadingSpotifyPlaylists] = useState(false);
  const [importingPlaylists, setImportingPlaylists] = useState<Set<string>>(new Set());
  const [isYoutubeMusicConfigured, setIsYoutubeMusicConfigured] = useState(false);
  const [notification, setNotification] = useState<{type: 'success' | 'error', message: string} | null>(null);

  useEffect(() => {
    loadData();
    // Verificar si hay un código de Spotify pendiente después del login
    checkPendingSpotifyCode();
  }, []);

  // Cargar playlists de Spotify cuando se conecte
  useEffect(() => {
    if (isSpotifyConnected) {
      loadSpotifyPlaylists();
    }
  }, [isSpotifyConnected]);

  // Auto-ocultar notificaciones después de 5 segundos
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  // Debug: monitorear cambios en playlists
  useEffect(() => {
    console.log('Estado de playlists cambió:', playlists.length, playlists);
  }, [playlists]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [playlistsData, transfersData] = await Promise.all([
        playlistAPI.getAll(),
        transferAPI.getAll()
      ]);
      setPlaylists(playlistsData);
      setTransferJobs(transfersData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkPendingSpotifyCode = async () => {
    const pendingCode = localStorage.getItem('spotify_pending_code');
    if (pendingCode) {
      try {
        console.log('Procesando código de Spotify pendiente...');
        const response = await spotifyAPI.handleCallback(pendingCode);
        if (response.success) {
          console.log('Código de Spotify procesado exitosamente');
          setNotification({type: 'success', message: '¡Cuenta de Spotify conectada exitosamente!'});
          setSpotifyRefreshTrigger(prev => prev + 1); // Trigger refresh del estado de Spotify
        }
      } catch (error) {
        console.error('Error procesando código de Spotify pendiente:', error);
        setNotification({type: 'error', message: 'Error al conectar con Spotify. Por favor, intenta conectar manualmente.'});
      } finally {
        // Limpiar el código pendiente
        localStorage.removeItem('spotify_pending_code');
      }
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
      // Extraer ID de la URL usando la utilidad
      const playlistId = utils.extractSpotifyPlaylistId(spotifyUrl);
      if (!playlistId) {
        throw new Error('URL de Spotify inválida');
      }

      const importedPlaylist = await playlistAPI.importFromSpotify({
        spotify_playlist_id: playlistId
      });
      
      // Agregar la nueva playlist al estado local inmediatamente
      setPlaylists(prevPlaylists => [...prevPlaylists, importedPlaylist]);
      
      setNotification({type: 'success', message: 'Playlist importada exitosamente'});
      // Ya no necesitamos loadData() porque actualizamos el estado directamente
    } catch (error: any) {
      console.error('Error importing playlist:', error);
      const errorMessage = error.response?.data?.error || 'Error al importar la playlist';
      setNotification({type: 'error', message: errorMessage});
    }
  };

  const loadSpotifyPlaylists = async () => {
    if (!isSpotifyConnected) return;
    
    try {
      setLoadingSpotifyPlaylists(true);
      const playlists = await spotifyAPI.getPlaylists();
      setSpotifyPlaylists(playlists);
    } catch (error: any) {
      console.error('Error loading Spotify playlists:', error);
      
      // Verificar si el error requiere reconexión
      if (error.response?.data?.requires_reconnection || error.response?.status === 401) {
        setNotification({
          type: 'error', 
          message: 'Tu sesión de Spotify ha expirado. Por favor, reconecta tu cuenta.'
        });
        setIsSpotifyConnected(false);
        setSpotifyPlaylists([]);
      } else {
        setNotification({type: 'error', message: 'Error al cargar playlists de Spotify'});
      }
    } finally {
      setLoadingSpotifyPlaylists(false);
    }
  };

  const handleImportSpotifyPlaylist = async (playlistId: string, name?: string, description?: string) => {
    // Agregar al estado de importación
    setImportingPlaylists(prev => new Set([...prev, playlistId]));
    
    try {
      console.log('Importando playlist:', playlistId, name);
      const importedPlaylist = await playlistAPI.importFromSpotify({
        spotify_playlist_id: playlistId,
        name,
        description
      });
      
      console.log('Playlist importada:', importedPlaylist);
      
      // Agregar la nueva playlist al estado local inmediatamente
      setPlaylists(prevPlaylists => {
        const updated = [...prevPlaylists, importedPlaylist];
        console.log('Estado de playlists actualizado:', updated);
        return updated;
      });
      
      setNotification({type: 'success', message: `Playlist "${name}" importada exitosamente`});
    } catch (error: any) {
      console.error('Error importing playlist:', error);
      const errorMessage = error.response?.data?.error || 'Error al importar la playlist';
      setNotification({type: 'error', message: errorMessage});
    } finally {
      // Remover del estado de importación
      setImportingPlaylists(prev => {
        const updated = new Set(prev);
        updated.delete(playlistId);
        return updated;
      });
    }
  };

  // Eliminar la función no usada

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
      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 max-w-sm w-full ${
          notification.type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } text-white p-4 rounded-lg shadow-lg`}>
          <div className="flex items-center justify-between">
            <span>{notification.message}</span>
            <button
              onClick={() => setNotification(null)}
              className="ml-2 text-white hover:text-gray-200"
            >
              ✕
            </button>
          </div>
        </div>
      )}

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
          {/* Spotify Connection Status */}
          <div className="mb-6">
            <SpotifyStatus 
              onConnectionChange={setIsSpotifyConnected} 
              refreshTrigger={spotifyRefreshTrigger}
            />
          </div>

          {/* YouTube Music Setup */}
          <div className="mb-6">
            <YouTubeMusicSetup 
              onConfigurationChange={setIsYoutubeMusicConfigured}
            />
          </div>

          {activeTab === 'playlists' ? (
            <div className="space-y-6">
              <PlaylistList
                playlists={playlists}
                onStartTransfer={handleStartTransfer}
                onImportPlaylist={handleImportPlaylist}
                onRefresh={loadData}
                isSpotifyConnected={isSpotifyConnected}
              />
              
              {/* Spotify Playlists Section */}
              {isSpotifyConnected && (
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      🎵 Tus Playlists de Spotify
                    </h3>
                    <button
                      onClick={loadSpotifyPlaylists}
                      disabled={loadingSpotifyPlaylists}
                      className="px-4 py-2 text-green-600 hover:text-green-800 font-medium disabled:opacity-50"
                    >
                      {loadingSpotifyPlaylists ? '🔄 Cargando...' : '🔄 Actualizar'}
                    </button>
                  </div>
                  
                  {loadingSpotifyPlaylists ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
                      <p className="mt-2 text-gray-600">Cargando playlists de Spotify...</p>
                    </div>
                  ) : spotifyPlaylists.length === 0 ? (
                    <div className="text-center py-8">
                      <div className="text-gray-400 text-4xl mb-2">🎵</div>
                      <p className="text-gray-500">No se encontraron playlists en Spotify</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {spotifyPlaylists.map((playlist) => (
                        <div
                          key={playlist.id}
                          className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-start space-x-3">
                            {/* Imagen de la playlist */}
                            <div className="flex-shrink-0">
                              {playlist.images && playlist.images.length > 0 ? (
                                <img
                                  src={playlist.images[0].url}
                                  alt={playlist.name}
                                  className="w-16 h-16 rounded-lg object-cover border"
                                />
                              ) : (
                                <div className="w-16 h-16 rounded-lg bg-gray-200 flex items-center justify-center">
                                  <span className="text-gray-400 text-2xl">🎵</span>
                                </div>
                              )}
                            </div>
                            
                            {/* Información de la playlist */}
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-gray-900 truncate">
                                {playlist.name}
                              </h4>
                              <p className="text-sm text-gray-500 mt-1">
                                {playlist.track_count} canciones • {playlist.owner}
                              </p>
                              {playlist.public === false && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 mt-1">
                                  🔒 Privada
                                </span>
                              )}
                              {playlist.collaborative && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mt-1 ml-1">
                                  👥 Colaborativa
                                </span>
                              )}
                              {playlist.description && (
                                <p className="text-xs text-gray-400 mt-2 line-clamp-2">
                                  {playlist.description}
                                </p>
                              )}
                            </div>
                            
                            {/* Botón de importar */}
                            <div className="flex-shrink-0">
                              <button
                                onClick={() => handleImportSpotifyPlaylist(
                                  playlist.id, 
                                  playlist.name, 
                                  playlist.description
                                )}
                                disabled={importingPlaylists.has(playlist.id)}
                                className={`px-3 py-2 text-white text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors ${
                                  importingPlaylists.has(playlist.id) 
                                    ? 'bg-gray-400 cursor-not-allowed' 
                                    : 'bg-green-600 hover:bg-green-700'
                                }`}
                              >
                                {importingPlaylists.has(playlist.id) ? '⏳ Importando...' : '📥 Importar'}
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {/* Fin de Spotify Playlists */}
            </div>
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
