import { useState, useCallback } from 'react';
import { detectarErroresService } from '../services/detectarErroresService';
import type { DetectarErroresResponse, CorregirErroresResponse, ErrorLogicoBD } from '../types';

interface UseDetectarErroresProps {
  nodes: any[];
  relations: any[];
  onApplyCorrections?: (fixedNodes: any[], fixedRelations: any[]) => void;
}

export function useDetectarErrores({ nodes, relations, onApplyCorrections }: UseDetectarErroresProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [repairing, setRepairing] = useState<boolean>(false);
  const [errorReport, setErrorReport] = useState<DetectarErroresResponse | null>(null);
  const [selectedError, setSelectedError] = useState<ErrorLogicoBD | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const ejecutarAnalisis = useCallback(async (xmlContent?: string) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await detectarErroresService.detectarErrores({
        xml_content: xmlContent,
        nodes: nodes.length > 0 ? nodes : undefined,
        relations: relations.length > 0 ? relations : undefined
      });
      setErrorReport(data);
      if (data.errores.length > 0) {
        setSelectedError(data.errores[0]);
      } else {
        setSelectedError(null);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Error al ejecutar detección de errores');
    } finally {
      setLoading(false);
    }
  }, [nodes, relations]);

  const ejecutarReparacion = useCallback(async (erroresIds?: string[], xmlContent?: string) => {
    setRepairing(true);
    setErrorMessage(null);
    try {
      const result: CorregirErroresResponse = await detectarErroresService.corregirErrores({
        xml_content: xmlContent,
        nodes,
        relations,
        errores_ids: erroresIds
      });

      if (onApplyCorrections) {
        onApplyCorrections(result.fixed_nodes, result.fixed_relations);
      }

      // Re-analizar tras reparar
      await ejecutarAnalisis(result.fixed_xml || undefined);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error al aplicar corrección automática');
    } finally {
      setRepairing(false);
    }
  }, [nodes, relations, onApplyCorrections, ejecutarAnalisis]);

  return {
    loading,
    repairing,
    errorReport,
    selectedError,
    setSelectedError,
    errorMessage,
    ejecutarAnalisis,
    ejecutarReparacion
  };
}

