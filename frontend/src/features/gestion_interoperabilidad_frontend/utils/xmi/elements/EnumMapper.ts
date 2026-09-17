import type { NodeType } from '@/features/gestion_modelado/shared/types/types';
import { ClassMapper } from './ClassMapper';

export class EnumMapper extends ClassMapper {
    protected getXmiType(): string {
        return 'UML:DataType';
    }
    
    protected getNodeType(): NodeType {
        return 'enum';
    }
    
    protected getColor(): string {
        return '#68d391';
    }
}
