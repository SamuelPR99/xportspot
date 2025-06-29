import type { TransferJob } from '../types';
import { youtubeUtils } from '../services';

interface TransferHistoryProps {
  transferJobs: TransferJob[];
  onRefresh: () => void;
}

const TransferHistory: React.FC<TransferHistoryProps> = ({
  transferJobs,
  onRefresh
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'processing':
        return 'text-blue-600 bg-blue-100';
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'partial':
        return 'text-orange-600 bg-orange-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '✅ Completado';
      case 'processing':
        return '🔄 Procesando';
      case 'pending':
        return '⏳ Pendiente';
      case 'failed':
        return '❌ Fallido';
      case 'partial':
        return '⚠️ Parcial';
      default:
        return status;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (startDate: string | null, endDate: string | null) => {
    if (!startDate || !endDate) return '-';
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diff = end.getTime() - start.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    return `${minutes}m ${seconds}s`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">
          Historial de Transferencias ({transferJobs.length})
        </h3>
        <button
          onClick={onRefresh}
          className="px-4 py-2 text-blue-600 hover:text-blue-800 font-medium"
        >
          🔄 Actualizar
        </button>
      </div>

      {transferJobs.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <div className="text-gray-400 text-6xl mb-4">📋</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No hay transferencias aún
          </h3>
          <p className="text-gray-500">
            Las transferencias que realices aparecerán aquí
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Playlist
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Progreso
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transferJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {job.playlist.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          → {job.youtube_playlist_name}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(job.status)}`}>
                        {getStatusText(job.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-1">
                          <div className="flex justify-between text-sm mb-1">
                            <span>{job.processed_songs} / {job.total_songs}</span>
                            <span>{job.progress_percentage}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                job.status === 'completed' ? 'bg-green-500' :
                                job.status === 'processing' ? 'bg-blue-500' :
                                job.status === 'failed' ? 'bg-red-500' :
                                'bg-gray-400'
                              }`}
                              style={{ width: `${job.progress_percentage}%` }}
                            ></div>
                          </div>
                          <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>✅ {job.successful_transfers}</span>
                            <span>❌ {job.failed_transfers}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>
                        <div>Iniciado: {formatDate(job.started_at)}</div>
                        {job.completed_at && (
                          <div>
                            Completado: {formatDate(job.completed_at)}
                            <br />
                            Duración: {formatDuration(job.started_at, job.completed_at)}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        {job.youtube_playlist_id && (
                          <a
                            href={youtubeUtils.getPlaylistUrl(job.youtube_playlist_id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-red-600 hover:text-red-900"
                            title="Ver en YouTube Music"
                          >
                            ▶️
                          </a>
                        )}
                        {job.error_message && (
                          <button
                            className="text-gray-600 hover:text-gray-900"
                            title={job.error_message}
                          >
                            ℹ️
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransferHistory;
