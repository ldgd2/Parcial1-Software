import type { DiagramState, ClassNode, Relation } from '@/features/gestion_modelado/shared/types/types';
import { ElementFactory } from './ElementFactory';
import { RelationFactory } from './RelationFactory';

export class XmiImporter {
    import(xmlText: string): DiagramState {
        const parser = new DOMParser();
        const doc = parser.parseFromString(xmlText, "text/xml");
        
        if (doc.getElementsByTagName("parsererror").length > 0) {
            throw new Error("XML no válido");
        }

        const nodes: ClassNode[] = [];
        const relations: Relation[] = [];
        const idMap: Record<string, string> = {}; // EAID -> internal id

        const packages = doc.getElementsByTagName("UML:Package");
        for (let i = 0; i < packages.length; i++) {
            const pkg = packages[i];
            
            // Nodos
            const elementTags = ["UML:Class", "UML:Interface", "UML:DataType", "UML:Note"];
            for (const tag of elementTags) {
                const elements = pkg.getElementsByTagName(tag);
                for (let j = 0; j < elements.length; j++) {
                    const el = elements[j];
                    const mapper = ElementFactory.getMapperByXmiTag(tag);
                    if (mapper) {
                        const node = mapper.fromXml(el, idMap);
                        if (node) nodes.push(node);
                    }
                }
            }
            
            // Relaciones
            const relationTags = ["UML:Generalization", "UML:Association"];
            for (const tag of relationTags) {
                const elements = pkg.getElementsByTagName(tag);
                for (let j = 0; j < elements.length; j++) {
                    const el = elements[j];
                    const mapper = RelationFactory.getMapperByXmiTag(tag);
                    if (mapper) {
                        const relation = mapper.fromXml(el, idMap);
                        if (relation) relations.push(relation);
                    }
                }
            }
        }
        
        // Geometría
        const diagEls = doc.getElementsByTagName("UML:DiagramElement");
        for (let i = 0; i < diagEls.length; i++) {
            const dEl = diagEls[i];
            const subject = dEl.getAttribute("subject") || "";
            const geometry = dEl.getAttribute("geometry") || "";
            
            const internalId = idMap[subject];
            if (internalId && geometry) {
                const leftMatch = geometry.match(/Left=(-?\d+)/);
                const topMatch = geometry.match(/Top=(-?\d+)/);
                const rightMatch = geometry.match(/Right=(-?\d+)/);
                
                const node = nodes.find(n => n.id === internalId);
                if (node) {
                    if (leftMatch) node.x = parseInt(leftMatch[1]);
                    // EA often uses negative or inverted Y coordinates relative to web canvas,
                    // but usually Top is positive and increases downwards.
                    if (topMatch) {
                        const top = parseInt(topMatch[1]);
                        // EA's Top can sometimes be negative, absolute value is often safer or just use as is
                        node.y = Math.abs(top); 
                    }
                    if (leftMatch && rightMatch) {
                        const width = parseInt(rightMatch[1]) - parseInt(leftMatch[1]);
                        node.width = Math.max(width, 140); // Enforce a reasonable minimum width
                    }
                }
            }
        }

        return {
            nodes,
            relations,
            correcciones: {},
            version: Date.now()
        };
    }
}
