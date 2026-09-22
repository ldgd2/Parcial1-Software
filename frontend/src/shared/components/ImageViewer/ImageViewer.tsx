import React, { useState, useRef, useEffect } from 'react';
import './ImageViewer.css';

interface ImageViewerProps {
    imageUrl: string;
    onClose: () => void;
}

export const ImageViewer: React.FC<ImageViewerProps> = ({ imageUrl, onClose }) => {
    const [scale, setScale] = useState(1);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const isDragging = useRef(false);
    const lastMousePos = useRef({ x: 0, y: 0 });

    const handleWheel = (e: React.WheelEvent) => {
        // Only prevent default if we're not over an element that needs scrolling (unlikely in viewer)
        const zoomDelta = e.deltaY > 0 ? -0.1 : 0.1;
        let newScale = scale + zoomDelta;
        
        // Limits for zoom
        if (newScale < 0.2) newScale = 0.2;
        if (newScale > 5) newScale = 5;
        
        setScale(newScale);
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        if (e.button !== 0) return; // Only left click
        e.preventDefault();
        isDragging.current = true;
        lastMousePos.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isDragging.current) return;
        
        const dx = e.clientX - lastMousePos.current.x;
        const dy = e.clientY - lastMousePos.current.y;
        
        setPosition(prev => ({ x: prev.x + dx, y: prev.y + dy }));
        lastMousePos.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseUp = () => {
        isDragging.current = false;
    };

    useEffect(() => {
        const handleGlobalMouseUp = () => {
            isDragging.current = false;
        };
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        
        window.addEventListener('mouseup', handleGlobalMouseUp);
        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.removeEventListener('mouseup', handleGlobalMouseUp);
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [onClose]);

    // Prevent scrolling body when zooming
    useEffect(() => {
        const originalOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = originalOverflow;
        };
    }, []);

    return (
        <div className="image-viewer-overlay" onWheel={handleWheel}>
            <button className="image-viewer-close" onClick={onClose} title="Cerrar (Esc)">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
            <div 
                className="image-viewer-container"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
            >
                <img 
                    src={imageUrl} 
                    alt="Visor" 
                    className="image-viewer-img"
                    style={{
                        transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                        cursor: isDragging.current ? 'grabbing' : 'grab'
                    }}
                    draggable={false}
                />
            </div>
            <div className="image-viewer-controls">
                <span>Zoom: {Math.round(scale * 100)}%</span>
                <span className="image-viewer-hint">(Usa la rueda del ratón para acercar/alejar y arrastra para moverte)</span>
            </div>
        </div>
    );
};
