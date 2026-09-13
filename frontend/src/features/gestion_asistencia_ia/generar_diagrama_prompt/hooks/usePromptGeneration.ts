import { useState, useRef } from 'react';
import { generarDiagramaPorPrompt } from '../services/promptService';
import type { PromptResponse } from '../types/promptTypes';

export const usePromptGeneration = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    
    // We use Web Speech API for voice recognition
    const recognitionRef = useRef<any>(null);

    const initSpeechRecognition = () => {
        // @ts-ignore - SpeechRecognition is not fully typed in standard TS yet
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            setError("El reconocimiento de voz no está soportado en este navegador.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'es-ES';
        recognition.continuous = false;
        recognition.interimResults = true;

        recognition.onresult = (event: any) => {
            let currentTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                currentTranscript += event.results[i][0].transcript;
            }
            setTranscript(currentTranscript);
        };

        recognition.onerror = (event: any) => {
            console.error("Speech recognition error", event.error);
            setError("Error en el reconocimiento de voz");
            setIsListening(false);
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognitionRef.current = recognition;
    };

    const startListening = () => {
        if (!recognitionRef.current) {
            initSpeechRecognition();
        }
        if (recognitionRef.current) {
            setError(null);
            setIsListening(true);
            recognitionRef.current.start();
        }
    };

    const stopListening = () => {
        if (recognitionRef.current && isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
        }
    };

    const generateDiagram = async (prompt: string): Promise<PromptResponse | null> => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await generarDiagramaPorPrompt(prompt);
            return data;
        } catch (err: any) {
            setError(err.message || "Error desconocido al generar diagrama");
            return null;
        } finally {
            setIsLoading(false);
        }
    };

    return {
        isLoading,
        error,
        generateDiagram,
        isListening,
        transcript,
        setTranscript,
        startListening,
        stopListening
    };
};
