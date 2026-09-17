import type { Relation } from '@/features/gestion_modelado/shared/types/types';
import type { IRelationMapper } from '../core/interfaces';
import { uid } from '../core/utils';

export class GeneralizationMapper implements IRelationMapper {
    toXml(relation: Relation): string {
        return `<UML:Generalization xmi.id="EAID_${relation.id}" subtype="EAID_${relation.sourceId}" supertype="EAID_${relation.targetId}" />`;
    }

    fromXml(element: Element, idMap: Record<string, string>): Relation | null {
        const subtype = element.getAttribute("subtype") || "";
        const supertype = element.getAttribute("supertype") || "";
        
        const internalSrc = idMap[subtype];
        const internalTgt = idMap[supertype];
        
        if (internalSrc && internalTgt) {
            return {
                id: uid(),
                type: 'inheritance',
                sourceId: internalSrc,
                targetId: internalTgt,
                version: 0,
                hash: ''
            };
        }
        return null;
    }
}
