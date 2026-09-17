import type { IElementMapper } from './interfaces';
import { ClassMapper } from '../elements/ClassMapper';
import { InterfaceMapper } from '../elements/InterfaceMapper';
import { EnumMapper } from '../elements/EnumMapper';
import { NoteMapper } from '../elements/NoteMapper';
import type { NodeType } from '@/features/gestion_modelado/shared/types/types';

export class ElementFactory {
    static getMapper(type: NodeType): IElementMapper {
        switch (type) {
            case 'interface':
                return new InterfaceMapper();
            case 'enum':
                return new EnumMapper();
            case 'note':
                return new NoteMapper();
            case 'class':
            default:
                return new ClassMapper();
        }
    }

    static getMapperByXmiTag(tag: string): IElementMapper | null {
        switch (tag) {
            case 'UML:Class': return new ClassMapper();
            case 'UML:Interface': return new InterfaceMapper();
            case 'UML:DataType': return new EnumMapper();
            case 'UML:Note': return new NoteMapper();
            default: return null;
        }
    }
}
