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
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = (event: any) => {
            let currentTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                currentTranscript += event.results[i][0].transcript;
            }
            if (currentTranscript.trim()) {
                setTranscript(currentTranscript);
            }
        };

        recognition.onerror = (event: any) => {
            console.error("Speech recognition error", event.error);
            if (event.error === 'no-speech') {
                // No emitir un error grave, solo es silencio
                return;
            }
            setError("Error de micrófono: " + event.error);
            setIsListening(false);
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognitionRef.current = recognition;
    };

    const startListening = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
        } catch (err) {
            console.error("Error al acceder al micrófono:", err);
            setError("No se pudo acceder al micrófono. Por favor, conceda los permisos.");
            return;
        }

        if (!recognitionRef.current) {
            initSpeechRecognition();
        }
        if (recognitionRef.current) {
            setError(null);
            setIsListening(true);
            try {
                recognitionRef.current.start();
            } catch (e) {
                console.error("Error al iniciar el reconocimiento:", e);
                setIsListening(false);
            }
        }
    };

    const stopListening = () => {
        if (recognitionRef.current && isListening) {
            try {
                recognitionRef.current.stop();
            } catch (e) {
                console.error("Error al detener el reconocimiento:", e);
            }
            setIsListening(false);
        }
    };

    const generateDiagram = async (prompt: string, context: string | null = null): Promise<PromptResponse | null> => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await generarDiagramaPorPrompt(prompt, context);
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
