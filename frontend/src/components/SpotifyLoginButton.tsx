import { useState } from 'react';
import { spotifyService } from '../services';

interface SpotifyLoginButtonProps {
  onSuccess: (response: any) => void;
  onError: (error: string) => void;
  className?: string;
  children?: React.ReactNode;
}

const SpotifyLoginButton: React.FC<SpotifyLoginButtonProps> = ({ 
  onSuccess, 
  onError, 
  className = "",
  children 
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      const { auth_url } = await spotifyService.getAuthUrl();
      if (auth_url) {
        // Marcar que estamos intentando hacer login con Spotify (no solo conectar)
        localStorage.setItem('spotify_login_mode', 'true');
        window.location.href = auth_url;
      } else {
        onError('No se pudo obtener URL de autorización');
      }
    } catch (error: any) {
      onError(error.message || 'Error al conectar con Spotify');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleLogin}
      disabled={isLoading}
      className={`flex items-center justify-center w-full px-4 py-3 border border-transparent rounded-md shadow-sm bg-green-600 text-white font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${className}`}
    >
      {isLoading ? (
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
          Conectando...
        </div>
      ) : (
        <>
          <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z"/>
          </svg>
          {children || 'Continuar con Spotify'}
        </>
      )}
    </button>
  );
};

export default SpotifyLoginButton;
