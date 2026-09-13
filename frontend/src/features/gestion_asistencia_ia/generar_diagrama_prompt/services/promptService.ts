import type { PromptResponse } from '../types/promptTypes';

export const generarDiagramaPorPrompt = async (prompt: string): Promise<PromptResponse> => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    const response = await fetch('http://localhost:8000/prompt/generar', {
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
