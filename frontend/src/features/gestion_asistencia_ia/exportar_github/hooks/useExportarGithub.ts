import { useState, useEffect } from 'react';
import { exportarGithubApi } from '../services/exportar_api';
import { TokenService } from '@/shared/lib/TokenService';

export const useExportarGithub = () => {
    const [githubUsername, setGithubUsername] = useState<string | null>(null);
    const [isExporting, setIsExporting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isLoadingStatus, setIsLoadingStatus] = useState(true);

    useEffect(() => {
        const checkStatusAndCallback = async () => {
            if (!TokenService.getToken()) {
                setIsLoadingStatus(false);
                return;
            }

            try {
                // Verificar si venimos de un redirect de GitHub con el código
                const urlParams = new URLSearchParams(window.location.search);
                const code = urlParams.get('code');
                
                if (code) {
                    const data = await exportarGithubApi.githubCallback(code);
                    setGithubUsername(data.github_username);
                    // Limpiar la URL
                    window.history.replaceState({}, document.title, window.location.pathname);
                } else {
                    // Si no hay código, verificamos el estado normal
                    const status = await exportarGithubApi.getStatus();
                    if (status.vinculado && status.github_username) {
                        setGithubUsername(status.github_username);
                    }
                }
            } catch (err: any) {
                setError(err.message || 'Error al verificar estado de GitHub');
            } finally {
                setIsLoadingStatus(false);
            }
        };

        checkStatusAndCallback();
    }, []);

    const iniciarVinculacion = async () => {
        if (!TokenService.getToken()) {
            setError('Debes iniciar sesión en la aplicación primero.');
            return;
        }
        try {
            setError(null);
            const { url } = await exportarGithubApi.getAuthUrl();
            window.location.href = url; // Redirige a GitHub
        } catch (err: any) {
            setError(err.message || 'Error al iniciar la vinculación con GitHub');
        }
    };

    const exportarProyecto = async (proyectoId: number, nombreRepo: string, diagramJson: any, autoDeploy: boolean = false) => {
        if (!githubUsername) {
            setError('No estás vinculado a GitHub. Por favor, vincúlate primero.');
            return null;
        }

        try {
            setIsExporting(true);
            setError(null);
            const response = await exportarGithubApi.exportarProyecto(proyectoId, nombreRepo, diagramJson, autoDeploy);
            setIsExporting(false);
            return response;
        } catch (err: any) {
            setIsExporting(false);
            setError(err.message || 'Error al exportar el proyecto');
            throw err;
        }
    };

    return {
        githubUsername,
        isExporting,
        isLoadingStatus,
        error,
        iniciarVinculacion,
        exportarProyecto
    };
};
