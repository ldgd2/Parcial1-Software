import type { NodeType } from '../../../gestion_modelado/shared/types/types';
import type { RelationType } from '../../../gestion_modelado/shared/types/types';

export interface PromptNode {
    id: string;
    type: NodeType;
    name: string;
    attributes: string[];
    methods: string[];
}

export interface PromptRelation {
    id: string;
    sourceId: string;
    targetId: string;
    type: RelationType;
    label: string;
}

export interface PromptResponse {
    nodes: PromptNode[];
    relations: PromptRelation[];
}
