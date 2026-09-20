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

    solicitarOtpDb: async () => {
        const response = await fetch(`${API_URL}/configuracion/solicitar-otp`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Error al solicitar código OTP');
        }
        return response.json();
    },

    configurarDbPassword: async (dbPassword: string, codigoOtp: string) => {
        const response = await fetch(`${API_URL}/configuracion/db`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ db_password: dbPassword, codigo_otp: codigoOtp })
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Error al configurar la contraseña');
        }
        return response.json();
    },

    desvincularGithub: async () => {
        const response = await fetch(`${API_URL}/configuracion/github`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Error al desvincular la cuenta de GitHub');
        }
        return response.json();
    }
};
