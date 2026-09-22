import React, { useState, useRef, useEffect } from 'react';
import { useDiagram } from '../../../gestion_modelado/shared/context/DiagramContext';
import { usePromptGeneration } from '../hooks/usePromptGeneration';
import { useImageDigitization } from '../../digitalizar_desde_imagen/hooks/useImageDigitization';
import { generateDeterministicHash } from '../../../gestion_modelado/shared/utils/hashGenerator';
import { parseUmlAttribute, parseUmlMethod } from '../../../gestion_modelado/shared/utils/umlParser';
import './ChatPanel.css';
import type { NodeType } from '../../../gestion_modelado/shared/types/types';
import { transcribeAudioAPI } from '../services/promptService';
interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    text: string;
    isError?: boolean;
}

interface ChatPanelProps {
    isOpen: boolean;
    onClose: () => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ isOpen, onClose }) => {
    const [messages, setMessages] = useState<Message[]>([
        { id: '1', role: 'assistant', text: '¡Hola! Soy tu asistente de IA. Escribe un requerimiento, dítalo por voz, o adjunta una imagen UML y yo lo transformaré en un diagrama en el lienzo.' }
    ]);
    const [prompt, setPrompt] = useState('');
    const [isListening, setIsListening] = useState(false);
    
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<BlobPart[]>([]);
    
    const { addNode, updateNode, addRelation, nodes, getDiagramState } = useDiagram();
    
    // Hooks de IA
    const { 
        generateDiagram, 
        isLoading: isGeneratingPrompt
    } = usePromptGeneration();

    const { 
        digitizeImage, 
        isLoading: isDigitizing
    } = useImageDigitization();

    const isLoading = isGeneratingPrompt || isDigitizing;

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, isLoading]);

    // ---- HANDLERS PARA INYECTAR EL RESULTADO AL LIENZO ----
    const injectResultToDiagram = (result: { nodes: any[], relations: any[] } | null) => {
        if (!result) return;
        const nodeMap = new Map<string, string>();
        let maxX = 0;
        let maxY = 0;
        
        // Encontrar los límites actuales del lienzo para insertar los nuevos nodos a la derecha
        nodes.forEach(n => {
            if (n.x > maxX) maxX = n.x;
            if (n.y > maxY) maxY = n.y;
        });

        const offsetX = maxX > 0 ? maxX + 300 : 100;
        let startY = 100;
        const GRID_SPACING_X = 250;
        const GRID_SPACING_Y = 250;
        let col = 0;
        let row = 0;

        // Insert nodes or Update them
        result.nodes.forEach(node => {
            const existingNode = nodes.find(n => n.id === node.id);
            if (existingNode) {
                // Actualizar nodo existente
                nodeMap.set(node.id, existingNode.id);
                
                const updatedData: any = {
                    nombre: node.name || existingNode.nombre,
                    atributos: (node.attributes || []).map((attr: string) => parseUmlAttribute(attr)),
                    metodos: (node.methods || []).map((met: string) => parseUmlMethod(met))
                };
                updateNode(existingNode.id, updatedData);
            } else {
                // Crear nuevo nodo con Grid Layout
                const newId = crypto.randomUUID();
                nodeMap.set(node.id, newId);
                
                const xPos = offsetX + (col * GRID_SPACING_X);
                const yPos = startY + (row * GRID_SPACING_Y);
                
                col++;
                if (col > 2) {
                    col = 0;
                    row++;
                }

                const nodeData: any = {
                    id: newId,
                    type: (node.type || 'class') as NodeType,
                    nombre: node.name || 'SinNombre',
                    atributos: (node.attributes || []).map((attr: string) => parseUmlAttribute(attr)),
                    metodos: (node.methods || []).map((met: string) => parseUmlMethod(met)),
                    color: '#ed8936',
                    x: xPos, 
                    y: yPos,
                    width: 220,
                    hash: '',
                    version: 0
                };
                
                generateDeterministicHash(nodeData).then((hash: string) => {
                    nodeData.hash = hash;
                    addNode(nodeData.type, nodeData);
                });
            }
        });

        // Insert relations (evitando duplicaciones idénticas de tipo y label)
        const currentRelations = getDiagramState().relations || [];
        
        result.relations.forEach(rel => {
            const sourceId = nodeMap.get(rel.sourceId) || rel.sourceId;
            const targetId = nodeMap.get(rel.targetId) || rel.targetId;
            if (sourceId && targetId && sourceId !== targetId) {
                const relType = (rel.type || 'association').toLowerCase();
                const relLabel = (rel.label || '').trim();

                const alreadyExists = currentRelations.some((existing: any) => {
                    const sameNodes = (existing.sourceId === sourceId && existing.targetId === targetId) ||
                                      (existing.sourceId === targetId && existing.targetId === sourceId);
                    const sameType = (existing.type || 'association').toLowerCase() === relType;
                    const sameLabel = (existing.label || '').trim() === relLabel;
                    return sameNodes && sameType && sameLabel;
                });
                
                if (!alreadyExists) {
                    const relData: any = {
                        id: crypto.randomUUID(),
                        sourceId,
                        targetId,
                        type: rel.type || 'association',
                        label: rel.label || '',
                        sourceLabel: '',
                        targetLabel: '',
                        hash: '',
                        version: 0
                    };
                    generateDeterministicHash({ type: 'relation', data: relData }).then((hash: string) => {
                        relData.hash = hash;
                        addRelation(relData);
                    });
                }
            }
        });
    };

    // ---- PROMPT (TEXTO / VOZ) ----
    const handleSendPrompt = async () => {
        if (!prompt.trim() || isLoading) return;
        
        const userText = prompt.trim();
        setPrompt('');
        
        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'user', text: userText }]);
        
        try {
            const currentState = getDiagramState();
            const contextStr = JSON.stringify(currentState);
            const result = await generateDiagram(userText, contextStr);
            if (!result) throw new Error("No se pudo generar el diagrama.");
            injectResultToDiagram(result);
            
            const responseText = result.summary || `¡Listo! He procesado ${result.nodes.length} clases y ${result.relations.length} relaciones basado en tu solicitud.`;
            setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: responseText }]);
        } catch (err: any) {
            setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: `Ocurrió un error: ${err.message || 'Intenta de nuevo más tarde.'}`, isError: true }]);
        }
    };

    // ---- VOZ CON MEDIARECORDER Y GEMINI ----
    const toggleVoice = async () => {
        if (isListening) {
            // Detener grabación
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                mediaRecorderRef.current.stop();
            }
            return;
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Usamos webm como formato nativo de MediaRecorder
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                setIsListening(false);
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                
                // Detener los tracks del micrófono
                stream.getTracks().forEach(track => track.stop());

                // Convert blob to base64
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = async () => {
                    const base64data = (reader.result as string).split(',')[1];
                    try {
                        const tempId = crypto.randomUUID();
                        setMessages(prev => [...prev, { id: tempId, role: 'system', text: 'Transcribiendo audio...' }]);
                        
                        const text = await transcribeAudioAPI(base64data, 'audio/webm');
                        
                        // Quitar el mensaje temporal y actualizar el prompt
                        setMessages(prev => prev.filter(m => m.id !== tempId));
                        
                        if (text) {
                            setPrompt(prev => prev + (prev ? ' ' : '') + text);
                        }
                    } catch (error: any) {
                        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: `Error al transcribir: ${error.message}`, isError: true }]);
                    }
                };
            };

            mediaRecorder.start();
            setIsListening(true);
        } catch (err) {
            console.error("Error accediendo al micrófono:", err);
            alert("No se pudo acceder al micrófono para grabar.");
        }
    };

    // ---- IMAGEN ----
    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;
        const file = e.target.files[0];
        
        if (!file.type.startsWith('image/')) {
            alert('Solo se permiten archivos de imagen.');
            return;
        }

        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'user', text: `[Imagen adjuntada: ${file.name}]` }]);
        
        try {
            const result = await digitizeImage(file);
            if (!result) throw new Error("No se pudo digitalizar la imagen.");
            injectResultToDiagram(result);
            setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: `¡Digitalización completa! Añadí ${result.nodes.length} elementos al diagrama.` }]);
        } catch (err: any) {
            setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: `Error al procesar la imagen: ${err.message || 'Intenta de nuevo.'}`, isError: true }]);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendPrompt();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="chat-panel">
            <div className="chat-panel__header">
                <h3>Asistente IA</h3>
                <button className="chat-panel__btn-close" onClick={onClose} title="Cerrar Panel">
                    <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>

            <div className="chat-panel__messages">
                {messages.map(msg => (
                    <div key={msg.id} className={`chat-message chat-message--${msg.role} ${msg.isError ? 'chat-message--error' : ''}`}>
                        <div className="chat-message__bubble">
                            {msg.text}
                        </div>
                    </div>
                ))}
                
                {isLoading && (
                    <div className="chat-message chat-message--assistant">
                        <div className="chat-message__bubble chat-message__loading">
                            <span className="dot"></span>
                            <span className="dot"></span>
                            <span className="dot"></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-panel__input-area">
                <textarea
                    placeholder="Describe un requerimiento, o adjunta una imagen UML..."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                    rows={2}
                />
                
                <div className="chat-panel__controls">
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        style={{ display: 'none' }} 
                        accept="image/*"
                        onChange={handleFileSelect}
                    />
                    <button className="chat-panel__action-btn" onClick={() => fileInputRef.current?.click()} disabled={isLoading} title="Adjuntar Imagen UML">
                        <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                    </button>
                    
                    <button className={`chat-panel__action-btn ${isListening ? 'listening' : ''}`} onClick={toggleVoice} disabled={isLoading} title="Dictar por Voz">
                        <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
                    </button>
                    
                    <div style={{ flex: 1 }}></div>

                    <button className="chat-panel__send-btn" onClick={handleSendPrompt} disabled={!prompt.trim() || isLoading} title="Enviar">
                        <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                    </button>
                </div>
            </div>
        </div>
    );
};
