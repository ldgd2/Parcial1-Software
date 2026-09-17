import type { Relation, RelationType } from '@/features/gestion_modelado/shared/types/types';
import type { IRelationMapper } from '../core/interfaces';
import { escapeXml, uid } from '../core/utils';

export class AssociationMapper implements IRelationMapper {
    toXml(relation: Relation): string {
        const xmiType = 'UML:Association';
        
        let xml = `<${xmiType} xmi.id="EAID_${relation.id}" visibility="public" isRoot="false" isLeaf="false" isAbstract="false">`;
        xml += `<UML:Association.connection>`;
        
        const aggSrc = relation.type === 'aggregation' ? 'shared' : relation.type === 'composition' ? 'composite' : 'none';
        
        xml += `<UML:AssociationEnd visibility="public" multiplicity="${escapeXml(relation.sourceLabel || '')}" aggregation="${aggSrc}" isOrdered="false" isNavigable="false" type="EAID_${relation.sourceId}" />`;
        xml += `<UML:AssociationEnd visibility="public" multiplicity="${escapeXml(relation.targetLabel || '')}" aggregation="none" isOrdered="false" isNavigable="true" type="EAID_${relation.targetId}" />`;
        
        xml += `</UML:Association.connection>`;
        xml += `</${xmiType}>`;
        return xml;
    }

    fromXml(element: Element, idMap: Record<string, string>): Relation | null {
        const ends = element.getElementsByTagName("UML:AssociationEnd");
        if (ends.length >= 2) {
            const srcEnd = ends[0];
            const tgtEnd = ends[1];
            
            const srcType = srcEnd.getAttribute("type") || "";
            const tgtType = tgtEnd.getAttribute("type") || "";
            
            const internalSrc = idMap[srcType];
            const internalTgt = idMap[tgtType];
            
            if (internalSrc && internalTgt) {
                const aggSrc = srcEnd.getAttribute("aggregation") || "none";
                let rType: RelationType = 'association';
                if (aggSrc === 'shared') rType = 'aggregation';
                if (aggSrc === 'composite') rType = 'composition';
                
                return {
                    id: uid(),
                    type: rType,
                    sourceId: internalSrc,
                    targetId: internalTgt,
                    sourceLabel: srcEnd.getAttribute("multiplicity") || "",
                    targetLabel: tgtEnd.getAttribute("multiplicity") || "",
                    version: 0,
                    hash: ''
                };
            }
        }
        return null;
    }
}
