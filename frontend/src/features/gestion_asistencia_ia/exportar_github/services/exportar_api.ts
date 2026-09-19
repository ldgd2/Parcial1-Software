import { TokenService } from '@/shared/lib/TokenService';

const API_URL = "http://localhost:8000"; // Asegúrate de que esto coincida con la URL de tu backend

const getAuthHeaders = () => {
    const token = TokenService.getToken();
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
};

export const exportarGithubApi = {
    getStatus: async (): Promise<{ vinculado: boolean, github_username?: string }> => {
        const response = await fetch(`${API_URL}/exportar-github/status`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            throw new Error('Error al obtener estado de vinculación');
        }
        return response.json();
    },

    getAuthUrl: async (): Promise<{ url: string }> => {
        const response = await fetch(`${API_URL}/exportar-github/auth-url`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            throw new Error('Error al obtener la URL de autorización');
        }
        return response.json();
    },

    githubCallback: async (code: string): Promise<{ mensaje: string, github_username: string }> => {
        const response = await fetch(`${API_URL}/exportar-github/callback`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ code }),
        });
        if (!response.ok) {
            throw new Error('Error al autenticar con GitHub');
        }
        return response.json();
    },

    exportarProyecto: async (proyecto_id: number, nombre_repo: string, diagram_json: any): Promise<{ url_repositorio: string, mensaje: string }> => {
        const response = await fetch(`${API_URL}/exportar-github/exportar`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                proyecto_id,
                nombre_repo,
                diagram_json
            }),
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Error al exportar el proyecto a GitHub');
        }
        return response.json();
    }
};
