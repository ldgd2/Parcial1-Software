import React from 'react';
import { usePromptGeneration } from '../hooks/usePromptGeneration';
import { useDiagram } from '../../../gestion_modelado/shared/context/DiagramContext';
import { generateDeterministicHash } from '../../../gestion_modelado/shared/utils/hashGenerator';
import { parseUmlAttribute, parseUmlMethod } from '../../../gestion_modelado/shared/utils/umlParser';

interface PromptModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const PromptModal: React.FC<PromptModalProps> = ({ isOpen, onClose }) => {
    const { 
        isLoading, 
        error, 
        generateDiagram, 
        clearError 
    } = usePromptGeneration();
    
    const { addNode, addRelation } = useDiagram();
    const [prompt, setPrompt] = React.useState('');

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (!prompt.trim()) return;
        
        const result = await generateDiagram(prompt);
        
        if (result) {
            // Add nodes to diagram
            const nodeMap = new Map<string, string>(); // oldId -> newId

            result.nodes.forEach(node => {
                const newId = crypto.randomUUID();
                nodeMap.set(node.id, newId);
                
                const nodeData: any = {
                    id: newId,
                    type: node.type,
                    nombre: node.name,
                    atributos: node.attributes.map((attr: string) => parseUmlAttribute(attr)),
                    metodos: node.methods.map((met: string) => parseUmlMethod(met)),
                    color: '#ed8936',
                    x: Math.random() * 400 + 100, 
                    y: Math.random() * 400 + 100,
                    width: 220,
                    hash: '',
                    version: 0
                };
                
                generateDeterministicHash(nodeData).then((hash: string) => {
                    nodeData.hash = hash;
                    addNode(nodeData.type, nodeData);
                });
            });

            // Add relations
            result.relations.forEach(rel => {
                const sourceId = nodeMap.get(rel.sourceId);
                const targetId = nodeMap.get(rel.targetId);
                if (sourceId && targetId) {
                    const relData: any = {
                        id: crypto.randomUUID(),
                        sourceId,
                        targetId,
                        type: rel.type,
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
            });

            onClose();
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-[#1e1e1e] p-6 rounded-xl border border-gray-700 w-[500px] shadow-2xl flex flex-col gap-4">
                <h2 className="text-xl font-semibold text-white">Generar Diagrama con IA</h2>
                
                <div className="flex flex-col gap-2">
                    <textarea 
                        className="w-full h-32 bg-[#2d2d2d] border border-gray-600 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500 resize-none"
                        placeholder="Describe el diagrama que deseas crear... (ej. 'Crea un sistema de ventas con clases Cliente, Producto y Factura')"
                        value={transcript}
                        onChange={(e) => setTranscript(e.target.value)}
                    />
                </div>

                {error && <p className="text-red-400 text-sm">{error}</p>}

                <div className="flex justify-between items-center mt-2">
                    <button 
                        onClick={isListening ? stopListening : startListening}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                            isListening ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-gray-700 hover:bg-gray-600 text-white'
                        }`}
                    >
                        {isListening ? (
                            <>
                                <span className="animate-pulse w-2 h-2 rounded-full bg-white"></span>
                                Detener Voz
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                                Dictar por Voz
                            </>
                        )}
                    </button>
                    
                    <div className="flex gap-2">
                        <button 
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 transition-colors"
                        >
                            Cancelar
                        </button>
                        <button 
                            onClick={handleSubmit}
                            disabled={isLoading || !transcript.trim()}
                            className="px-4 py-2 rounded-lg font-medium bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 transition-colors flex items-center gap-2"
                        >
                            {isLoading ? 'Generando...' : 'Generar Diagrama'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
