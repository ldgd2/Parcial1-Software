import React, { useState, useRef, useEffect } from 'react';
import { useDiagram } from '../../../gestion_modelado/shared/context/DiagramContext';
import { usePromptGeneration } from '../hooks/usePromptGeneration';
import { useImageDigitization } from '../../digitalizar_desde_imagen/hooks/useImageDigitization';
import { generateDeterministicHash } from '../../../gestion_modelado/shared/utils/hashGenerator';
import { parseUmlAttribute, parseUmlMethod } from '../../../gestion_modelado/shared/utils/umlParser';
import { ImageViewer } from '@/shared/components/ImageViewer/ImageViewer';
import './ChatPanel.css';
import type { NodeType } from '../../../gestion_modelado/shared/types/types';
import { transcribeAudioAPI } from '../services/promptService';
interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    text: string;
    imageUrl?: string;
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
    const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
    const [selectedImagePreview, setSelectedImagePreview] = useState<string | null>(null);
    const [voiceVolume, setVoiceVolume] = useState<number>(0);
    const [viewerImage, setViewerImage] = useState<string | null>(null);
    const [isDragOver, setIsDragOver] = useState(false);
    
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<BlobPart[]>([]);
    
    // Equalizer refs
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const animationFrameRef = useRef<number>(0);
    const streamRef = useRef<MediaStream | null>(null);
    
    const { addNode, updateNode, addRelation, nodes, getDiagramState, deleteNode, deleteRelation } = useDiagram();
    
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

    useEffect(() => {
        return () => {
            if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
            if (audioContextRef.current) audioContextRef.current.close();
        };
    }, []);

    // ---- HANDLERS PARA INYECTAR EL RESULTADO AL LIENZO ----
    const injectResultToDiagram = (result: { nodes: any[], relations: any[], deletedNodes?: string[], deletedRelations?: string[] } | null) => {
        if (!result) return;
        
        // Procesar eliminaciones
        const deletedNodeIds = new Set<string>();
        const deletedRelationIds = new Set<string>();

        if (result.deletedNodes && result.deletedNodes.length > 0) {
            result.deletedNodes.forEach(item => {
                const idOrName = typeof item === 'string' ? item.trim() : (item.id || item.name || item.nombre || '').toString().trim();
                if (!idOrName) return;

                // Encontrar todos los nodos que coincidan con el ID o el nombre
                const matchingNodes = nodes.filter(n => n.id === idOrName || n.nombre.toLowerCase() === idOrName.toLowerCase());
                
                if (matchingNodes.length > 0) {
                    matchingNodes.forEach(node => {
                        deletedNodeIds.add(node.id);
                        if (node.nombre) deletedNodeIds.add(node.nombre.toLowerCase());
                        deleteNode(node.id);
                    });
                } else {
                    // Fallback por si era un ID puro que no estaba en el estado local actual por alguna razón
                    deletedNodeIds.add(idOrName);
                    deleteNode(idOrName);
                }
                // Siempre añadir el término original por si acaso
                if (typeof idOrName === 'string') {
                    deletedNodeIds.add(idOrName.toLowerCase());
                }
            });
        }
        
        if (result.deletedRelations && result.deletedRelations.length > 0) {
            result.deletedRelations.forEach(item => {
                const id = typeof item === 'string' ? item.trim() : (item.id || '').toString().trim();
                if (!id) return;
                deletedRelationIds.add(id);
                deleteRelation(id);
            });
        }

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
            // Ignorar el nodo si está marcado para ser eliminado
            if (deletedNodeIds.has(node.id) || (node.name && deletedNodeIds.has(node.name.toLowerCase()))) {
                return;
            }

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

        
        const currentRelations = getDiagramState().relations || [];
        
        result.relations.forEach(rel => {
            if (deletedRelationIds.has(rel.id)) return;

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

    // ---- PROMPT (TEXTO / VOZ / IMAGEN) ----
    const handleSendPrompt = async (forcedText?: string) => {
        const textToSend = (forcedText || prompt).trim();
        if ((!textToSend && !selectedImageFile) || isLoading) return;
        
        setPrompt('');
        
        let userMessageText = textToSend;
        let imageUrl: string | undefined;

        if (selectedImageFile) {
            userMessageText = textToSend || 'Digitalizar imagen';
            imageUrl = selectedImagePreview || undefined;
        }
        
        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'user', text: userMessageText, imageUrl }]);
        
        try {
            if (selectedImageFile) {
                const result = await digitizeImage(selectedImageFile, textToSend);
                if (!result) throw new Error("No se pudo digitalizar la imagen.");
                injectResultToDiagram(result);
                setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: `¡Digitalización completa! Añadí ${result.nodes.length} elementos y ${result.relations.length} relaciones al diagrama.` }]);
                setSelectedImageFile(null);
                setSelectedImagePreview(null);
            } else {
                const currentState = getDiagramState();
                const contextStr = JSON.stringify(currentState);
                const result = await generateDiagram(textToSend, contextStr);
                injectResultToDiagram(result);
                
                const responseText = result.summary || `¡Listo! He procesado ${result.nodes.length} clases y ${result.relations.length} relaciones basado en tu solicitud.`;
                setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: responseText }]);
            }
        } catch (err: any) {
            setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: `Ocurrió un error: ${err.message || 'Intenta de nuevo más tarde.'}`, isError: true }]);
        }
    };

    // ---- VOZ CON MEDIARECORDER Y GEMINI ----
    const updateEqualizer = () => {
        if (!analyserRef.current) return;
        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(dataArray);
        
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }
        const average = sum / dataArray.length;
        setVoiceVolume(average);
        
        animationFrameRef.current = requestAnimationFrame(updateEqualizer);
    };

    const toggleVoice = async (action: 'start' | 'cancel' | 'send' = 'start') => {
        if (isListening) {
       
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
              
                (mediaRecorderRef.current as any).action = action;
                mediaRecorderRef.current.stop();
            }
            if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
            return;
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;
            
            // Setup Equalizer
            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
            audioContextRef.current = audioContext;
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 64;
            analyserRef.current = analyser;
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            updateEqualizer();
            
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
                const actionTaken = (mediaRecorder as any).action;
                setIsListening(false);
                setVoiceVolume(0);
                if (audioContextRef.current) audioContextRef.current.close();
                
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                
                // Detener los tracks del micrófono
                if (streamRef.current) {
                    streamRef.current.getTracks().forEach(track => track.stop());
                }

                if (actionTaken === 'cancel') {
                    // No hacemos nada, solo se canceló
                    return;
                }

                // Convert blob to base64
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = async () => {
                    const base64data = (reader.result as string).split(',')[1];
                    try {
                        const tempId = crypto.randomUUID();
                        setMessages(prev => [...prev, { id: tempId, role: 'system', text: 'Transcribiendo audio...' }]);
                        
                        const text = await transcribeAudioAPI(base64data, 'audio/webm');
                        
                        // Quitar el mensaje temporal
                        setMessages(prev => prev.filter(m => m.id !== tempId));
                        
                        if (text) {
                            handleSendPrompt(text); // Envío directo a IA
                        }
                    } catch (error: any) {
                        setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', text: `Error al transcribir: ${error.message}`, isError: true }]);
                    }
                };
            };

            mediaRecorder.start();
            setIsListening(true);
        } catch (err: any) {
            console.error("Error accediendo al micrófono:", err);
            if (err.name === 'NotFoundError' || err.message.includes('not found')) {
                alert("No se detectó un micrófono en tu dispositivo. Asegúrate de tener uno conectado.");
            } else if (err.name === 'NotAllowedError' || err.message.includes('denied')) {
                alert("Permiso denegado. Debes permitir el acceso al micrófono en tu navegador.");
            } else {
                alert(`No se pudo acceder al micrófono: ${err.message || 'Error desconocido'}`);
            }
        }
    };

    // ---- IMAGEN ----
    const processImageFile = (file: File) => {
        setSelectedImageFile(file);
        
        const reader = new FileReader();
        reader.onload = (e) => {
            setSelectedImagePreview(e.target?.result as string);
        };
        reader.readAsDataURL(file);
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;
        const file = e.target.files[0];
        
        if (!file.type.startsWith('image/')) {
            alert('Solo se permiten archivos de imagen.');
            return;
        }

        processImageFile(file);
    };

    const handlePaste = (e: React.ClipboardEvent) => {
        if (e.clipboardData.files && e.clipboardData.files.length > 0) {
            const file = e.clipboardData.files[0];
            if (file.type.startsWith('image/')) {
                e.preventDefault();
                processImageFile(file);
            }
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer.types.includes('Files')) {
            setIsDragOver(true);
        }
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);
        
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            if (file.type.startsWith('image/')) {
                processImageFile(file);
            } else {
                alert('Solo se permiten archivos de imagen.');
            }
        }
    };

    const removeSelectedImage = () => {
        setSelectedImageFile(null);
        setSelectedImagePreview(null);
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
                            {msg.imageUrl && (
                                <img 
                                    src={msg.imageUrl} 
                                    alt="Adjunto" 
                                    style={{ maxWidth: '100%', borderRadius: '4px', marginBottom: '8px', display: 'block', cursor: 'pointer' }} 
                                    onClick={() => setViewerImage(msg.imageUrl!)}
                                />
                            )}
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

            <div 
                className={`chat-panel__input-area ${isDragOver ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {selectedImagePreview && (
                    <div className="chat-panel__image-preview-wrapper">
                        <img src={selectedImagePreview} alt="Preview" className="chat-panel__image-preview" />
                        <button className="chat-panel__image-remove-btn" onClick={removeSelectedImage} title="Quitar imagen">
                            <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                )}
                
                {isListening ? (
                    <div className="chat-panel__voice-modal">
                        <div className="voice-equalizer">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div 
                                    key={i} 
                                    className="equalizer-bar" 
                                    style={{ height: `${Math.max(10, voiceVolume * (Math.random() * 0.8 + 0.2))}px` }} 
                                />
                            ))}
                        </div>
                        <span className="voice-status">Escuchando...</span>
                    </div>
                ) : (
                    <textarea
                        placeholder={selectedImageFile ? "Añade un comentario a la imagen..." : "Pega (Ctrl+V), arrastra una imagen, o escribe un requerimiento..."}
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onPaste={handlePaste}
                        disabled={isLoading}
                        rows={2}
                    />
                )}
                
                <div className="chat-panel__controls">
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        style={{ display: 'none' }} 
                        accept="image/*"
                        onChange={handleFileSelect}
                    />
                    {!isListening && (
                        <button className="chat-panel__action-btn" onClick={() => fileInputRef.current?.click()} disabled={isLoading} title="Adjuntar Imagen UML">
                            <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                        </button>
                    )}
                    
                    <button className={`chat-panel__action-btn ${isListening ? 'listening' : ''}`} onClick={() => toggleVoice(isListening ? 'cancel' : 'start')} disabled={isLoading} title={isListening ? "Detener y Cancelar" : "Dictar por Voz"}>
                        <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
                    </button>
                    
                    <div style={{ flex: 1 }}></div>

                    {isListening ? (
                        <button className="chat-panel__send-btn" onClick={() => toggleVoice('send')} title="Enviar Audio a IA">
                            <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                        </button>
                    ) : (
                        <button className="chat-panel__send-btn" onClick={() => handleSendPrompt()} disabled={(!prompt.trim() && !selectedImageFile) || isLoading} title="Enviar">
                            <svg width="1em" height="1em" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                        </button>
                    )}
                </div>
            </div>

            {viewerImage && (
                <ImageViewer imageUrl={viewerImage} onClose={() => setViewerImage(null)} />
            )}
        </div>
    );
};
