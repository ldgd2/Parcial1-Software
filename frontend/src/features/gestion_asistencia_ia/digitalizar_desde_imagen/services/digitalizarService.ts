import type { DigitalizarResponse } from '../types/digitalizarTypes';
import { API_URL } from '@/shared/lib/api';
import { TokenService } from '@/shared/lib/TokenService';

export const digitalizarImagen = async (
    imageBase64: string,
    prompt?: string,
    provider?: string,
    apiKey?: string
): Promise<DigitalizarResponse> => {
    const token = TokenService.getToken();
    const body: Record<string, any> = { image_base64: imageBase64 };
    if (prompt) body.prompt = prompt;
    if (provider) body.provider = provider;
    if (apiKey && apiKey.trim()) body.api_key = apiKey.trim();
    
    const response = await fetch(`${API_URL}/digitalizar/imagen`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        let errorMessage = 'Error al digitalizar la imagen';
        try {
            const errData = await response.json();
            if (errData?.detail) errorMessage = errData.detail;
        } catch {}
        throw new Error(errorMessage);
    }

    return await response.json();
};
