import type { ClassNode, Relation } from '@/features/gestion_modelado/shared/types/types';

export interface IElementMapper {
    toXml(node: ClassNode): string;
    fromXml(element: Element, idMap: Record<string, string>): ClassNode | null;
}

export interface IRelationMapper {
    toXml(relation: Relation): string;
    fromXml(element: Element, idMap: Record<string, string>): Relation | null;
}
