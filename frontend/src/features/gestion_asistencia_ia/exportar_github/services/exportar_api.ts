import { TokenService } from '@/shared/lib/TokenService';
import { API_URL } from '@/shared/lib/api';

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

    /**
     * Exporta en segundo plano: generar + compilar + corregir con IA + push puede tardar varios
     * minutos y Cloudflare corta cualquier petición a los 100 s (error 524, visto como CORS).
     * Se inicia el trabajo y se consulta su estado hasta que termina.
     */
    exportarProyecto: async (
        proyecto_id: number,
        nombre_repo: string,
        diagram_json: any,
        auto_deploy: boolean = false,
        onProgreso?: (segundos: number) => void,
    ): Promise<{ url_repositorio: string, mensaje: string, api_docs_md?: string }> => {
        const inicio = await fetch(`${API_URL}/exportar-github/exportar/iniciar`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ proyecto_id, nombre_repo, diagram_json, auto_deploy }),
        });
        if (!inicio.ok) {
            const errData = await inicio.json().catch(() => ({}));
            throw new Error(errData.detail || 'Error al iniciar la exportación a GitHub');
        }
        const { trabajo_id } = await inicio.json();

        const limite = Date.now() + 20 * 60 * 1000;
        let fallosSeguidos = 0;
        while (Date.now() < limite) {
            await new Promise((r) => setTimeout(r, 3000));
            const res = await fetch(`${API_URL}/exportar-github/exportar/estado/${trabajo_id}`, {
                headers: getAuthHeaders(),
            }).catch(() => null);
            if (res && res.status === 404) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'La exportación se perdió (¿se reinició el servidor?)');
            }
            if (!res || !res.ok) {
                // Cortes de red momentáneos: reintentar; si persisten, avisar
                if (++fallosSeguidos >= 10) throw new Error('Se perdió la conexión con el servidor durante la exportación');
                continue;
            }
            fallosSeguidos = 0;
            const estado = await res.json();
            onProgreso?.(estado.segundos ?? 0);
            if (estado.estado === 'ok') return estado.resultado;
            if (estado.estado === 'error') throw new Error(estado.error || 'Error al exportar el proyecto a GitHub');
        }
        throw new Error('La exportación está tardando demasiado. Revisa el repositorio en GitHub en unos minutos.');
    }
};
