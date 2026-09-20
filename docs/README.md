# Documentación del Trabajo de Investigación Formativa (TIF)

> Auditoría de Sistemas / TI — Universidad Nacional de San Agustín de Arequipa (UNSA)  
> Sistema Autónomo de Auditoría de Privacidad y DSPM (ISO/IEC 27701:2025 y Ley 29733)

Este directorio contiene la investigación formal, diseño arquitectónico y fundamentación técnica del sistema.

---

## Índice de Documentos Técnicos

| Documento | Descripción |
|---|---|
| [01. Análisis de Dominio Normativo](01_analisis_dominio_normativo.md) | Estudio de ISO/IEC 27701:2025 como norma de gestión independiente (*standalone*), sus 78 controles, principios de ISO/IEC 29100 y marco jurídico peruano (Ley N.° 29733 y D.S. 016-2024-JUS). |
| [02. Análisis Crítico de la Propuesta Inicial](02_analisis_critico_propuesta_inicial.md) | Evaluación de la arquitectura inicial y diagnóstico de las fallas fatales del RAG vectorial tradicional frente a grafos deterministas. |
| [03. Propuestas de Arquitectura](03_propuestas_arquitectura.md) | Comparación técnica entre alternativas de arquitectura y selección del modelo híbrido GraphRAG + DSPM Analyzer. |
| [04. Diseño Detallado y Módulos](04_diseno_detallado_y_modulos.md) | Especificación de los componentes del sistema: Ingesta DDL, Clasificador de Columnas, Motor de Reglas DSPM y Privacy Coach Agent. |
| [05. Plan de Implementación](05_plan_implementacion_tif.md) | Fases de desarrollo, cronograma de trabajo e hitos académicos del proyecto de investigación. |
| [06. Estado del Arte](06_estado_del_arte_sistemas_similares.md) | Benchmarking con plataformas líderes de la industria (OneTrust, BigID, Securiti.ai, Microsoft Purview) y revisión sistemática de literatura (Oxford, IEEE, ACM). |
| [07. Referencias y Corpus Documental](07_referencias_y_corpus_documental_rag.md) | Modelado del Grafo de Conocimiento Normativo (`networkx`), filtrado de 78 controles y compresión de contexto de +150,000 tokens a ~850 tokens. |
| [08. Arquitectura Senior del Sistema Multi-Agente](08_arquitectura_senior_sistema_agentes.md) | Especificación formal de la máquina de estados, contratos de datos entre agentes, interfaces y protocolo de comunicación. |
| [09. Flujo End-to-End: Del Esquema SQL a la Remediación](09_flujo_ejemplo_end_to_end_dspm_coach.md) | Trazabilidad completa con el caso de prueba real (Clínica SaludTotal), desde el análisis sintáctico AST hasta el parche SQL en producción. |

---

## Visualizadores Interactivos

- [Arquitectura Interactiva del Sistema](arquitectura_interactiva.html): Visualizador HTML del flujo entre componentes y almacenes de datos.
- [Esquema de Agentes](arquitectura_sistema_agentes.html): Diagrama interactivo de la interacción entre el motor DSPM, el subgrafo y el LLM.
- [Flujo End-to-End](flujo_end_to_end_dspm_coach.html): Diagrama secuencial interactivo del ciclo de auditoría y remediación.
