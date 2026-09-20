import { API_URL } from '@/shared/lib/api';
import { TokenService } from '@/shared/lib/TokenService';

const getAuthHeaders = () => {
    const token = TokenService.getToken();
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
};

export const configApi = {
    obtenerConfiguracion: async () => {
        const response = await fetch(`${API_URL}/configuracion`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Error al obtener la configuración');
        return response.json();
    },

    configurarDbPassword: async (dbPassword: string) => {
        const response = await fetch(`${API_URL}/configuracion/db`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ db_password: dbPassword })
        });
        if (!response.ok) throw new Error('Error al configurar la contraseña');
        return response.json();
    }
};
