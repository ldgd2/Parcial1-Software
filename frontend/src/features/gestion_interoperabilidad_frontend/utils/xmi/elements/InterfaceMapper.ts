import type { NodeType } from '@/features/gestion_modelado/shared/types/types';
import { ClassMapper } from './ClassMapper';

export class InterfaceMapper extends ClassMapper {
    protected getXmiType(): string {
        return 'UML:Interface';
    }
    
    protected getNodeType(): NodeType {
        return 'interface';
    }
    
    protected getColor(): string {
        return '#b794f4';
    }
}
