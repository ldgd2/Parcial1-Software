import { useState } from 'react';
import { digitalizarImagen } from '../services/digitalizarService';
import type { DigitalizarResponse } from '../types/digitalizarTypes';

export const useImageDigitization = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const digitizeImage = async (file: File): Promise<DigitalizarResponse | null> => {
        setIsLoading(true);
        setError(null);
        
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = async () => {
                const base64String = reader.result as string;
                try {
                    const data = await digitalizarImagen(base64String);
                    resolve(data);
                } catch (err: any) {
                    setError(err.message || "Error al digitalizar la imagen");
                    resolve(null);
                } finally {
                    setIsLoading(false);
                }
            };
            reader.onerror = () => {
                setError("Error al leer el archivo de imagen");
                setIsLoading(false);
                resolve(null);
            };
        });
    };

    return {
        isLoading,
        error,
        digitizeImage
    };
};
