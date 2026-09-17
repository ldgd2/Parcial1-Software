import type { NodeType } from '@/features/gestion_modelado/shared/types/types';
import { ClassMapper } from './ClassMapper';

export class NoteMapper extends ClassMapper {
    protected getXmiType(): string {
        return 'UML:Note';
    }
    
    protected getNodeType(): NodeType {
        return 'note';
    }
    
    protected getColor(): string {
        return '#f6e05e';
    }
}
