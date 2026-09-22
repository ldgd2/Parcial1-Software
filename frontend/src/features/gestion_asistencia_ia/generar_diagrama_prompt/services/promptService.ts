import type { PromptResponse } from '../types/promptTypes';
import { TokenService } from '@/shared/lib/TokenService';
import { API_URL } from '@/shared/lib/api';

export const generarDiagramaPorPrompt = async (prompt: string, context: string | null = null): Promise<PromptResponse> => {
    const token = TokenService.getToken();
    const body: any = { prompt };
    if (context) {
        body.context = context;
    }

    const response = await fetch(`${API_URL}/prompt/generar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        throw new Error('Error al generar el diagrama');
    }

    return await response.json();
};

export const transcribeAudioAPI = async (base64Data: string, mimeType: string = 'audio/webm'): Promise<string> => {
    const token = TokenService.getToken();
    const response = await fetch(`${API_URL}/prompt/transcribe-audio`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ audio_base64: base64Data, mime_type: mimeType })
    });

    if (!response.ok) {
        throw new Error('Error al transcribir el audio');
    }

    const data = await response.json();
    return data.text;
};
