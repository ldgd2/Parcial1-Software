import type { DigitalizarResponse } from '../types/digitalizarTypes';

export const digitalizarImagen = async (imageBase64: string): Promise<DigitalizarResponse> => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    const response = await fetch('http://localhost:8000/digitalizar/imagen', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ image_base64: imageBase64 })
    });

    if (!response.ok) {
        throw new Error('Error al digitalizar la imagen');
    }

    return await response.json();
};
