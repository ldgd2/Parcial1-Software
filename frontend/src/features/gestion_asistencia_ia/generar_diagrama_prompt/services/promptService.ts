import type { PromptResponse } from '../types/promptTypes';
import { TokenService } from '@/shared/lib/TokenService';
import { API_URL } from '@/shared/lib/api';

export const generarDiagramaPorPrompt = async (prompt: string): Promise<PromptResponse> => {
    const token = TokenService.getToken();
    const response = await fetch(`${API_URL}/prompt/generar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ prompt })
    });

    if (!response.ok) {
        throw new Error('Error al generar el diagrama');
    }

    return await response.json();
};
