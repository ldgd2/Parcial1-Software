import React, { useState, useRef } from 'react';
import { useImageDigitization } from '../hooks/useImageDigitization';
import { useDiagram } from '../../../gestion_modelado/shared/context/DiagramContext';
import { generateDeterministicHash } from '../../../gestion_modelado/shared/utils/hashGenerator';
import { parseUmlAttribute, parseUmlMethod } from '../../../gestion_modelado/shared/utils/umlParser';

interface ImageUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const ImageUploadModal: React.FC<ImageUploadModalProps> = ({ isOpen, onClose }) => {
    const { isLoading, error, digitizeImage } = useImageDigitization();
    const { addNode, addRelation } = useDiagram();
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    if (!isOpen) return null;

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const file = e.target.files[0];
            setSelectedFile(file);
            const url = URL.createObjectURL(file);
            setPreviewUrl(url);
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            if (file.type.startsWith('image/')) {
                setSelectedFile(file);
                const url = URL.createObjectURL(file);
                setPreviewUrl(url);
            }
        }
    };

    const handleSubmit = async () => {
        if (!selectedFile) return;
        
        const result = await digitizeImage(selectedFile);
        
        if (result) {
            // Add nodes to diagram
            const nodeMap = new Map<string, string>();

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
                <h2 className="text-xl font-semibold text-white">Digitalizar Diagrama desde Imagen</h2>
                
                <div 
                    className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors ${
                        previewUrl ? 'border-gray-600 bg-[#2d2d2d]' : 'border-gray-600 hover:border-blue-500 hover:bg-[#2a2a2a]'
                    }`}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleDrop}
                >
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        className="hidden" 
                        accept="image/*"
                        onChange={handleFileChange}
                    />
                    
                    {previewUrl ? (
                        <img src={previewUrl} alt="Preview" className="max-h-48 object-contain rounded" />
                    ) : (
                        <div className="text-center">
                            <svg className="w-12 h-12 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            <p className="text-gray-300 font-medium">Haz clic o arrastra una imagen aquí</p>
                            <p className="text-gray-500 text-sm mt-1">Soporta JPG, PNG, WEBP</p>
                        </div>
                    )}
                </div>

                {error && <p className="text-red-400 text-sm">{error}</p>}

                <div className="flex justify-end gap-2 mt-2">
                    <button 
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 transition-colors"
                    >
                        Cancelar
                    </button>
                    <button 
                        onClick={handleSubmit}
                        disabled={isLoading || !selectedFile}
                        className="px-4 py-2 rounded-lg font-medium bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 transition-colors flex items-center gap-2"
                    >
                        {isLoading ? 'Digitalizando...' : 'Digitalizar'}
                    </button>
                </div>
            </div>
        </div>
    );
};
