import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { authService } from './services';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import Register from './components/Register';
import SpotifyCallback from './components/SpotifyCallback';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showRegister, setShowRegister] = useState<boolean>(false);

  useEffect(() => {
    // Verificar si el usuario está autenticado al cargar la app
    const checkAuth = () => {
      const authenticated = authService.isAuthenticated();
      setIsAuthenticated(authenticated);
      setIsLoading(false);
    };

    // Escuchar cambios de autenticación
    const handleAuthChange = () => {
      const authenticated = authService.isAuthenticated();
      setIsAuthenticated(authenticated);
    };

    checkAuth();
    
    // Agregar listener para cambios de autenticación
    window.addEventListener('auth-changed', handleAuthChange);
    
    // Cleanup
    return () => {
      window.removeEventListener('auth-changed', handleAuthChange);
    };
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleRegister = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
  };

  const handleSwitchToRegister = () => {
    setShowRegister(true);
  };

  const handleSwitchToLogin = () => {
    setShowRegister(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Routes>
          <Route path="/auth/spotify/callback" element={<SpotifyCallback />} />
          <Route path="/" element={
            isAuthenticated ? (
              <Dashboard onLogout={handleLogout} />
            ) : showRegister ? (
              <Register onRegister={handleRegister} onSwitchToLogin={handleSwitchToLogin} />
            ) : (
              <Login onLogin={handleLogin} onSwitchToRegister={handleSwitchToRegister} />
            )
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
