import React, { useState } from 'react';
import api from '../services/api';

interface SpotifyLoginProps {
  onSuccess: (user: any, token: string) => void;
  onError: (error: string) => void;
}

const SpotifyLogin: React.FC<SpotifyLoginProps> = ({ onSuccess, onError }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleSpotifyLogin = async () => {
    setIsLoading(true);
    try {
      // Obtener URL de autorización de Spotify
      const response = await api.get('/auth/spotify/url/');
      const authUrl = response.data.auth_url;
      
      // Abrir ventana de autorización
      const popup = window.open(
        authUrl,
        'spotify-auth',
        'width=400,height=600,scrollbars=yes,resizable=yes'
      );

      // Escuchar mensaje de la ventana popup
      const messageListener = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;
        
        if (event.data.type === 'SPOTIFY_AUTH_SUCCESS') {
          const { code } = event.data;
          handleSpotifyCallback(code);
          popup?.close();
          window.removeEventListener('message', messageListener);
        } else if (event.data.type === 'SPOTIFY_AUTH_ERROR') {
          onError('Error en la autenticación con Spotify');
          popup?.close();
          window.removeEventListener('message', messageListener);
          setIsLoading(false);
        }
      };

      window.addEventListener('message', messageListener);

      // Verificar si la ventana se cerró sin autorización
      const checkClosed = setInterval(() => {
        if (popup?.closed) {
          clearInterval(checkClosed);
          window.removeEventListener('message', messageListener);
          setIsLoading(false);
        }
      }, 1000);

    } catch (error) {
      console.error('Error al iniciar autenticación con Spotify:', error);
      onError('Error al conectar con Spotify');
      setIsLoading(false);
    }
  };

  const handleSpotifyCallback = async (code: string) => {
    try {
      const response = await api.post('/auth/spotify/callback/', { code });
      const { user, token } = response.data;
      
      // Guardar token y usuario
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      onSuccess(user, token);
    } catch (error) {
      console.error('Error en callback de Spotify:', error);
      onError('Error al procesar la autenticación con Spotify');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleSpotifyLogin}
      disabled={isLoading}
      className="w-full bg-green-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-green-700 transition duration-200 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isLoading ? (
        <>
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
          <span>Conectando...</span>
        </>
      ) : (
        <>
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z"/>
          </svg>
          <span>Continuar con Spotify</span>
        </>
      )}
    </button>
  );
};

export default SpotifyLogin;
