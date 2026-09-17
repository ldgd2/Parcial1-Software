import type { ClassNode, NodeType } from '@/features/gestion_modelado/shared/types/types';
import type { IElementMapper } from '../core/interfaces';
import { escapeXml, uid } from '../core/utils';

export class ClassMapper implements IElementMapper {
    protected getXmiType(): string {
        return 'UML:Class';
    }
    
    protected getNodeType(): NodeType {
        return 'class';
    }
    
    protected getColor(): string {
        return '#ed8936';
    }

    toXml(node: ClassNode): string {
        const xmiType = this.getXmiType();
        let xml = `<${xmiType} name="${escapeXml(node.nombre)}" xmi.id="EAID_${node.id}" visibility="public" namespace="EAPK_local" isRoot="false" isLeaf="false" isAbstract="false" isActive="false">`;
        
        if (node.atributos && node.atributos.length > 0) {
            xml += `<UML:Classifier.feature>`;
            node.atributos.forEach(attr => {
                const vis = attr.visibilidad === '+' ? 'public' : attr.visibilidad === '-' ? 'private' : attr.visibilidad === '#' ? 'protected' : 'public';
                xml += `<UML:Attribute name="${escapeXml(attr.nombre)}" xmi.id="EAID_ATTR_${attr.id}" visibility="${vis}" ownerScope="instance" changeability="changeable">`;
                xml += `<UML:StructuralFeature.type><UML:Classifier xmi.idref="EAID_TYPE_${attr.tipo.replace(/\W/g,'_')}" /></UML:StructuralFeature.type>`;
                xml += `</UML:Attribute>`;
            });
            
            if (node.metodos && node.metodos.length > 0) {
                node.metodos.forEach(met => {
                    const vis = met.visibilidad === '+' ? 'public' : met.visibilidad === '-' ? 'private' : met.visibilidad === '#' ? 'protected' : 'public';
                    xml += `<UML:Operation name="${escapeXml(met.nombre)}" xmi.id="EAID_OP_${met.id}" visibility="${vis}" ownerScope="instance" isQuery="false" concurrency="sequential">`;
                    xml += `<UML:BehavioralFeature.parameter>`;
                    xml += `<UML:Parameter kind="return" visibility="public"><UML:Parameter.type><UML:Classifier xmi.idref="EAID_TYPE_${met.retorno.replace(/\W/g,'_')}" /></UML:Parameter.type></UML:Parameter>`;
                    xml += `</UML:BehavioralFeature.parameter>`;
                    xml += `</UML:Operation>`;
                });
            }
            xml += `</UML:Classifier.feature>`;
        }
        xml += `</${xmiType}>`;
        return xml;
    }

    fromXml(element: Element, idMap: Record<string, string>): ClassNode | null {
        const eaId = element.getAttribute("xmi.id") || "";
        if (!eaId) return null;
        
        const internalId = uid();
        idMap[eaId] = internalId;
        
        const name = element.getAttribute("name") || "Untitled";
        
        let stereotype = "";
        const stereos = element.getElementsByTagName("UML:Stereotype");
        if (stereos.length > 0) {
            stereotype = stereos[0].getAttribute("name") || "";
        }
        
        // Determinar un type más preciso si el estereotipo nos da pistas (para que no todo diga «clase»)
        let finalType = this.getNodeType();
        if (finalType === 'class') {
            const lowStereo = stereotype.toLowerCase();
            if (lowStereo === 'datatype' || lowStereo === 'primitive' || lowStereo === 'signal' || lowStereo === 'enumeration') {
                finalType = lowStereo === 'enumeration' ? 'enum' : lowStereo as any;
            }
        }
        
        const cls: ClassNode = {
            id: internalId,
            type: finalType,
            x: 100, y: 100, width: 220,
            nombre: name,
            color: this.getColor(),
            version: 0,
            hash: '',
            atributos: [],
            metodos: []
        };
        
        if (stereotype && finalType === 'class') {
             cls.estereotipo = stereotype;
        }

        const attrs = element.getElementsByTagName("UML:Attribute");
        for (let k = 0; k < attrs.length; k++) {
            const attr = attrs[k];
            const attrName = attr.getAttribute("name") || "attr";
            const vis = attr.getAttribute("visibility") === "private" ? "-" : attr.getAttribute("visibility") === "protected" ? "#" : "+";
            
            let attrType = "String";
            const typeEls = attr.getElementsByTagName("UML:StructuralFeature.type");
            if (typeEls.length > 0) {
                const classifier = typeEls[0].getElementsByTagName("UML:Classifier");
                if (classifier.length > 0) {
                    const tref = classifier[0].getAttribute("xmi.idref") || "";
                    attrType = tref.replace("EAID_TYPE_", "");
                }
            }

            cls.atributos.push({
                id: uid(),
                visibilidad: vis as any,
                nombre: attrName,
                tipo: attrType,
                version: 0
            });
        }
        
        const ops = element.getElementsByTagName("UML:Operation");
        for (let k = 0; k < ops.length; k++) {
            const op = ops[k];
            const opName = op.getAttribute("name") || "op";
            const vis = op.getAttribute("visibility") === "private" ? "-" : op.getAttribute("visibility") === "protected" ? "#" : "+";
            
            let retType = "void";
            const paramEls = op.getElementsByTagName("UML:Parameter");
            for (let p = 0; p < paramEls.length; p++) {
                const param = paramEls[p];
                if (param.getAttribute("kind") === "return") {
                    const ptypes = param.getElementsByTagName("UML:Parameter.type");
                    if (ptypes.length > 0) {
                        const classifier = ptypes[0].getElementsByTagName("UML:Classifier");
                        if (classifier.length > 0) {
                            const tref = classifier[0].getAttribute("xmi.idref") || "";
                            retType = tref.replace("EAID_TYPE_", "");
                        }
                    }
                }
            }

            cls.metodos.push({
                id: uid(),
                visibilidad: vis as any,
                nombre: opName,
                parametros: "",
                retorno: retType,
                version: 0
            });
        }

        return cls;
    }
}
