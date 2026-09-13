import type { PromptNode, PromptRelation } from '../../generar_diagrama_prompt/types/promptTypes';

export interface DigitalizarResponse {
    nodes: PromptNode[];
    relations: PromptRelation[];
}
