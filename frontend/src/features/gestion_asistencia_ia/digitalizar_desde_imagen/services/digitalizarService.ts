import type { DigitalizarResponse } from '../types/digitalizarTypes';
import { API_URL } from '@/shared/lib/api';
import { TokenService } from '@/shared/lib/TokenService';

export const digitalizarImagen = async (imageBase64: string, prompt?: string): Promise<DigitalizarResponse> => {
    const token = TokenService.getToken();
    const body: any = { image_base64: imageBase64 };
    if (prompt) body.prompt = prompt;
    
    const response = await fetch(`${API_URL}/digitalizar/imagen`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        throw new Error('Error al digitalizar la imagen');
    }

    return await response.json();
};
