import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services';

const SpotifyCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const processCallback = async () => {
      try {
        const urlParams = new URLSearchParams(location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');

        if (error) {
          setError('Error en la autenticación con Spotify: ' + error);
          setIsProcessing(false);
          return;
        }

        if (!code) {
          setError('No se recibió el código de autorización de Spotify');
          setIsProcessing(false);
          return;
        }

        // Verificar si estamos en modo de login/registro automático
        const isLoginMode = localStorage.getItem('spotify_login_mode') === 'true';
        
        if (isLoginMode) {
          // Limpiar el flag de login mode
          localStorage.removeItem('spotify_login_mode');
          
          // Intentar login/registro automático con Spotify
          const response = await authService.spotifyAuthOrRegister(code);
          
          if (response.success) {
            // Guardar token y datos del usuario
            if (response.token) {
              authService.setToken(response.token);
              // Disparar evento personalizado para que App.tsx se entere del login
              window.dispatchEvent(new CustomEvent('auth-changed'));
            }
            
            setSuccess(response.data?.message || '¡Autenticación exitosa!');
            setIsProcessing(false);
            setTimeout(() => {
              navigate('/', { replace: true });
            }, 2000);
            return;
          } else {
            setError(response.error || 'Error en autenticación automática');
            setIsProcessing(false);
            return;
          }
        }

        // Verificar si el usuario está autenticado (modo de conexión)
        const isAuth = authService.isAuthenticated();
        const token = authService.getToken();
        console.log('Usuario autenticado:', isAuth, 'Token:', token ? 'presente' : 'ausente');
        
        if (!isAuth) {
          // Guardar el código de Spotify temporalmente
          localStorage.setItem('spotify_pending_code', code);
          setError('Debes estar logueado para conectar con Spotify. El código se ha guardado temporalmente. Por favor, inicia sesión y luego conecta tu cuenta de Spotify desde el dashboard.');
          setIsProcessing(false);
          setTimeout(() => {
            navigate('/', { replace: true });
          }, 5000);
          return;
        }

        // Enviar el código al backend para completar la autenticación
        const response = await authService.spotifyCallback(code);
        
        if (response.success) {
          // Conexión exitosa, mostrar mensaje de éxito
          setSuccess('¡Cuenta de Spotify conectada exitosamente!');
          setIsProcessing(false);
          setTimeout(() => {
            navigate('/', { replace: true });
          }, 2000);
        } else {
          setError(response.error || 'Error al completar la autenticación');
          setIsProcessing(false);
        }
      } catch (err) {
        console.error('Error en callback de Spotify:', err);
        setError('Error inesperado al procesar la autenticación');
        setIsProcessing(false);
      }
    };

    processCallback();
  }, [location.search, navigate]);

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      {isProcessing ? (
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Procesando autenticación con Spotify...</p>
        </div>
      ) : success ? (
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full mx-4">
          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">¡Éxito!</h2>
            <p className="text-gray-600 mb-6">{success}</p>
            <p className="text-sm text-gray-500">Redirigiendo al dashboard...</p>
          </div>
        </div>
      ) : error ? (
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full mx-4">
          <div className="text-center">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Error de Autenticación</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => navigate('/', { replace: true })}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200"
            >
              Volver al Dashboard
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default SpotifyCallback;
