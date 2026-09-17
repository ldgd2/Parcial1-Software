import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { exportarGithubApi } from '../services/exportar_api';

export const GithubCallbackView: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState<string>('Vinculando cuenta con GitHub...');
    const procesado = React.useRef(false);

    useEffect(() => {
        if (procesado.current) return;
        
        const code = searchParams.get('code');
        
        if (!code) {
            setStatus('Error: No se recibió código de GitHub.');
            setTimeout(() => navigate('/dashboard'), 3000);
            return;
        }

        const vincular = async () => {
            procesado.current = true;
            try {
                const response = await exportarGithubApi.githubCallback(code);
                setStatus(`¡Éxito! Cuenta vinculada como ${response.github_username}. Redirigiendo...`);
                
                // Redirigir al dashboard (o al último diagrama si se guardó)
                setTimeout(() => {
                    const lastDiagram = localStorage.getItem('lastDiagramId');
                    if (lastDiagram) {
                        navigate(`/diagrama/${lastDiagram}`);
                    } else {
                        navigate('/dashboard');
                    }
                }, 2000);
            } catch (error: any) {
                console.error(error);
                setStatus(`Error al vincular: ${error.message || 'Error desconocido'}`);
                setTimeout(() => navigate('/dashboard'), 3000);
            }
        };

        vincular();
    }, [searchParams, navigate]);

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#1a1a1a', color: 'white', fontFamily: 'Inter, sans-serif' }}>
            <div style={{ textAlign: 'center', padding: '2rem', background: '#2a2a2a', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.3)' }}>
                <h2>Conexión GitHub</h2>
                <p>{status}</p>
            </div>
        </div>
    );
};
