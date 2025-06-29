import { useState, useEffect } from 'react';
import { spotifyService } from '../services';

interface SpotifyUser {
  is_connected: boolean;
  spotify_user_id?: string;
  spotify_display_name?: string;
  token_valid?: boolean;
  needs_reconnection?: boolean;
}

interface SpotifyStatusProps {
  onConnectionChange?: (isConnected: boolean) => void;
  refreshTrigger?: number; // Para forzar actualización desde el componente padre
}

const SpotifyStatus: React.FC<SpotifyStatusProps> = ({ onConnectionChange, refreshTrigger }) => {
  const [status, setStatus] = useState<SpotifyUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  useEffect(() => {
    loadStatus();
  }, [refreshTrigger]); // Agregado refreshTrigger como dependencia

  const loadStatus = async () => {
    try {
      setLoading(true);
      const statusData = await spotifyService.getConnectionStatus();
      setStatus(statusData);
      onConnectionChange?.(statusData.is_connected);
    } catch (error) {
      console.error('Error loading Spotify status:', error);
      setStatus({ is_connected: false });
      onConnectionChange?.(false);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const { auth_url } = await spotifyService.getAuthUrl();
      if (auth_url) {
        window.location.href = auth_url;
      } else {
        console.error('No se pudo obtener URL de autorización');
      }
    } catch (error) {
      console.error('Error al conectar con Spotify:', error);
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('¿Estás seguro de que quieres desconectar tu cuenta de Spotify?')) {
      return;
    }

    setDisconnecting(true);
    try {
      await spotifyService.disconnect();
      await loadStatus(); // Recargar estado
    } catch (error) {
      console.error('Error al desconectar Spotify:', error);
    } finally {
      setDisconnecting(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-500"></div>
          <span className="ml-2 text-gray-600">Cargando estado de Spotify...</span>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <span className="text-red-500 text-2xl mr-3">⚠️</span>
          <div>
            <h3 className="text-red-800 font-medium">Error al cargar estado</h3>
            <p className="text-red-600 text-sm">No se pudo verificar la conexión con Spotify</p>
          </div>
        </div>
      </div>
    );
  }

  if (status.is_connected) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-green-500 text-2xl mr-3">🎵</span>
            <div>
              <h3 className="text-green-800 font-medium">Spotify Conectado</h3>
              <p className="text-green-600 text-sm">
                {status.spotify_display_name ? 
                  `Conectado como: ${status.spotify_display_name}` : 
                  'Cuenta conectada exitosamente'
                }
              </p>
              {status.needs_reconnection && (
                <p className="text-orange-600 text-sm mt-1">
                  ⚠️ Se requiere reconexión para actualizar permisos
                </p>
              )}
            </div>
          </div>
          <div className="flex space-x-2">
            {status.needs_reconnection && (
              <button
                onClick={handleConnect}
                disabled={connecting}
                className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50 text-sm"
              >
                {connecting ? 'Reconectando...' : 'Reconectar'}
              </button>
            )}
            <button
              onClick={handleDisconnect}
              disabled={disconnecting}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 text-sm"
            >
              {disconnecting ? 'Desconectando...' : 'Desconectar'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-green-400 to-green-600 rounded-lg p-6 text-white">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-white text-2xl mr-3">🎵</span>
          <div>
            <h3 className="text-white font-medium">Conecta tu Spotify</h3>
            <p className="text-green-100 text-sm">
              Conecta tu cuenta para importar tus playlists
            </p>
          </div>
        </div>
        <button
          onClick={handleConnect}
          disabled={connecting}
          className="bg-white text-green-600 px-6 py-2 rounded-full font-medium hover:bg-gray-100 transition-colors disabled:opacity-50"
        >
          {connecting ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600 mr-2"></div>
              Conectando...
            </div>
          ) : (
            'Conectar Spotify'
          )}
        </button>
      </div>
    </div>
  );
};

export default SpotifyStatus;
