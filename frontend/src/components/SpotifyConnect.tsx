import { useState } from 'react';

interface SpotifyConnectProps {
  onConnect: () => void;
}

const SpotifyConnect: React.FC<SpotifyConnectProps> = ({ onConnect }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleConnect = async () => {
    setIsLoading(true);
    try {
      // Obtener URL de autorización
      const response = await fetch('/api/auth/spotify/url/');
      const data = await response.json();
      
      if (data.auth_url) {
        // Redirigir a Spotify para autorización
        window.location.href = data.auth_url;
      } else {
        console.error('No se pudo obtener URL de autorización');
      }
    } catch (error) {
      console.error('Error al conectar con Spotify:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-r from-green-400 to-green-600 rounded-lg p-6 text-white">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">🎵 Conecta tu Spotify</h3>
          <p className="text-green-100 text-sm mt-1">
            Conecta tu cuenta para importar tus playlists
          </p>
        </div>
        <button
          onClick={handleConnect}
          disabled={isLoading}
          className="bg-white text-green-600 px-6 py-2 rounded-full font-medium hover:bg-gray-100 transition-colors disabled:opacity-50"
        >
          {isLoading ? (
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

export default SpotifyConnect;
