import { useState, useEffect } from 'react';
import { youtubeMusicAPI } from '../services/api';
import type { YouTubeMusicStatus, YouTubeMusicGuide } from '../types';

interface YouTubeMusicSetupProps {
  onConfigurationChange: (isConfigured: boolean) => void;
}

const YouTubeMusicSetup: React.FC<YouTubeMusicSetupProps> = ({ onConfigurationChange }) => {
  const [status, setStatus] = useState<YouTubeMusicStatus>({ is_configured: false });
  const [guide, setGuide] = useState<YouTubeMusicGuide | null>(null);
  const [browserData, setBrowserData] = useState('');
  const [showSetup, setShowSetup] = useState(false);
  const [configuring, setConfiguring] = useState(false);
  const [loading, setLoading] = useState(true);
  const [testingConnection, setTestingConnection] = useState(false);
  const [notification, setNotification] = useState<{type: 'success' | 'error', message: string} | null>(null);

  useEffect(() => {
    loadStatus();
    loadGuide();
  }, []);

  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const loadStatus = async () => {
    try {
      const statusData = await youtubeMusicAPI.getStatus();
      setStatus(statusData);
      onConfigurationChange(statusData.is_configured);
    } catch (error) {
      console.error('Error loading YouTube Music status:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadGuide = async () => {
    try {
      const guideData = await youtubeMusicAPI.getSetupGuide();
      setGuide(guideData);
    } catch (error) {
      console.error('Error loading setup guide:', error);
    }
  };

  const handleConfigure = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!browserData.trim()) return;

    setConfiguring(true);
    try {
      // Validar que sea JSON válido
      JSON.parse(browserData);
      
      await youtubeMusicAPI.configure({ browser_data: browserData });
      
      setNotification({ type: 'success', message: '¡YouTube Music configurado exitosamente!' });
      setBrowserData('');
      setShowSetup(false);
      loadStatus();
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Error al configurar YouTube Music';
      setNotification({ type: 'error', message: errorMessage });
    } finally {
      setConfiguring(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('¿Estás seguro de que quieres desconfigurar YouTube Music?')) return;

    try {
      await youtubeMusicAPI.disconnect();
      setNotification({ type: 'success', message: 'YouTube Music desconfigurado' });
      loadStatus();
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Error al desconfigurar YouTube Music';
      setNotification({ type: 'error', message: errorMessage });
    }
  };

  const handleTestConnection = async () => {
    try {
      setTestingConnection(true);
      const result = await youtubeMusicAPI.testConnection();
      
      if (result.success) {
        const message = result.details?.note 
          ? `${result.message}\n\n${result.details.note}`
          : result.message;
          
        setNotification({
          type: 'success', 
          message: message
        });
      } else {
        setNotification({
          type: 'error', 
          message: result.error || 'Error al probar la conexión'
        });
      }
    } catch (error: any) {
      console.error('Error testing connection:', error);
      setNotification({
        type: 'error', 
        message: error.response?.data?.error || 'Error al probar la conexión'
      });
    } finally {
      setTestingConnection(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-3 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      {notification && (
        <div className={`mb-4 p-4 rounded-lg ${
          notification.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          <div className="flex items-center justify-between">
            <span>{notification.message}</span>
            <button onClick={() => setNotification(null)} className="ml-2 hover:opacity-70">✕</button>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          📺 Configuración de YouTube Music
        </h3>
        {status.is_configured && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
            ✅ Configurado
          </span>
        )}
      </div>

      {status.is_configured ? (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-green-500 text-xl mr-3">✅</span>
              <div>
                <h4 className="text-green-800 font-medium">YouTube Music Configurado</h4>
                <p className="text-green-600 text-sm">
                  Configurado el {status.configured_at ? new Date(status.configured_at).toLocaleDateString('es-ES') : 'fecha desconocida'}
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={handleTestConnection}
              disabled={testingConnection}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
            >
              {testingConnection ? '🔄 Probando...' : '🧪 Probar Conexión'}
            </button>
            <button
              onClick={() => setShowSetup(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              🔧 Reconfigurar
            </button>
            <button
              onClick={handleDisconnect}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              🗑️ Desconfigurar
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-yellow-500 text-xl mr-3">⚠️</span>
              <div>
                <h4 className="text-yellow-800 font-medium">YouTube Music no configurado</h4>
                <p className="text-yellow-600 text-sm">
                  Necesitas configurar YouTube Music para poder transferir playlists
                </p>
              </div>
            </div>
          </div>
          
          <button
            onClick={() => setShowSetup(true)}
            className="px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 font-medium"
          >
            🚀 Configurar YouTube Music
          </button>
        </div>
      )}

      {/* Modal de configuración */}
      {showSetup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold text-gray-900">
                  🛠️ Configurar YouTube Music
                </h3>
                <button
                  onClick={() => setShowSetup(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {guide && (
                <div className="space-y-6">
                  {/* Guía paso a paso */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">{guide.title}</h4>
                    <p className="text-blue-700 text-sm">{guide.description}</p>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Pasos */}
                    <div>
                      <h4 className="font-medium text-gray-900 mb-4">📋 Pasos a seguir:</h4>
                      <div className="space-y-3">
                        {guide.steps.map((step) => (
                          <div key={step.step} className="border rounded-lg p-3">
                            <div className="flex items-start">
                              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full text-xs font-medium flex items-center justify-center mr-3">
                                {step.step}
                              </span>
                              <div>
                                <h5 className="font-medium text-gray-900 text-sm">{step.title}</h5>
                                <p className="text-gray-600 text-xs mt-1">{step.description}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Solución de problemas */}
                    <div>
                      <h4 className="font-medium text-gray-900 mb-4">🔧 Solución de problemas:</h4>
                      <div className="space-y-3">
                        {guide.troubleshooting.map((item, index) => (
                          <div key={index} className="border border-orange-200 rounded-lg p-3 bg-orange-50">
                            <h5 className="font-medium text-orange-900 text-sm">{item.problem}</h5>
                            <p className="text-orange-700 text-xs mt-1">{item.solution}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Formulario */}
                  <form onSubmit={handleConfigure} className="space-y-4">
                    <div>
                      <label htmlFor="browserData" className="block text-sm font-medium text-gray-700 mb-2">
                        📄 Pega aquí el JSON del browser.json:
                      </label>
                      <textarea
                        id="browserData"
                        value={browserData}
                        onChange={(e) => setBrowserData(e.target.value)}
                        className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-xs"
                        placeholder='{"headers": {"accept": "*/*", "accept-language": "en-US,en;q=0.9", ...}}'
                        required
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        💡 Tip: Ve a curlconverter.com, pega tu cURL y copia el JSON resultante
                      </p>
                    </div>

                    <div className="flex space-x-3">
                      <button
                        type="button"
                        onClick={() => setShowSetup(false)}
                        className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                      >
                        Cancelar
                      </button>
                      <button
                        type="submit"
                        disabled={configuring || !browserData.trim()}
                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {configuring ? (
                          <div className="flex items-center justify-center">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Configurando...
                          </div>
                        ) : (
                          '💾 Configurar'
                        )}
                      </button>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default YouTubeMusicSetup;
