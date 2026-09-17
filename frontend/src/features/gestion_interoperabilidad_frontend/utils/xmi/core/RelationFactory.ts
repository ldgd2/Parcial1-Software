import type { IRelationMapper } from './interfaces';
import { AssociationMapper } from '../relations/AssociationMapper';
import { GeneralizationMapper } from '../relations/GeneralizationMapper';
import type { RelationType } from '@/features/gestion_modelado/shared/types/types';

export class RelationFactory {
    static getMapper(type: RelationType): IRelationMapper {
        switch (type) {
            case 'inheritance':
                return new GeneralizationMapper();
            case 'association':
            case 'aggregation':
            case 'composition':
            case 'dependency':
            default:
                return new AssociationMapper();
        }
    }

    static getMapperByXmiTag(tag: string): IRelationMapper | null {
        switch (tag) {
            case 'UML:Association': return new AssociationMapper();
            case 'UML:Generalization': return new GeneralizationMapper();
            default: return null;
        }
    }
}
