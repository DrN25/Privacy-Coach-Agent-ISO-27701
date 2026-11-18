// ==============================================================================
// Drawer Persistente Contextual: Asistente IA PIMS (SQLGlot + ISO 27701 + UNSA A2A)
// Disponible en los 5 módulos de la aplicación.
// ==============================================================================

window.ChatDrawer = function ChatDrawer({
  open,
  onClose,
  uiContext,
  selectedIncident,
  messages,
  onSendMessage,
  chatInput,
  setChatInput,
  chatLoading,
}) {
  const { useState, useRef, useEffect } = React;
  const [expandedFlows, setExpandedFlows] = useState({});
  const [expandedSqls, setExpandedSqls] = useState({});
  const bottomRef = useRef(null);

  useEffect(() => {
    if (bottomRef.current && open) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, chatLoading, open]);

  if (!open) return null;

  const suggestions = [
    '¿Cuáles son los registros que quedaron como pendientes del 2023-2025?',
    '¿Qué responsables aún tienen incidentes sin cerrar que son críticos?',
    ...(selectedIncident
      ? [`En ${selectedIncident.incident_code}, ¿qué acciones faltan para cerrarlo según ISO 27701 A.3.12?`]
      : ['¿Qué exige ISO/IEC 27701:2025 control A.3.12 (B.3.12)?']),
  ];

  const moduleLabels = {
    incidentes: 'Incidentes y Brechas',
    medidas: 'Medidas Correctivas 10.2',
    inspector: 'Inspector SQL / PDF',
    controles: 'Controles ISO y Docs',
    directorios: 'Responsables y Activos',
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[460px] bg-surface-card border-l border-surface-border z-40 flex flex-col shadow-2xl">
      {/* Cabecera */}
      <div className="p-3.5 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
        <div>
          <div className="font-serif font-bold text-sm text-ink-primary">
            Asistente IA PIMS • Consulta SQL & Normativa
          </div>
          <div className="text-[10px] font-mono text-ink-muted">
            SQLGlot Tiempo Real • 78 Controles ISO 27701:2025 • UNSA A2A
          </div>
        </div>
        <button
          onClick={onClose}
          className="px-2 py-1 rounded text-xs font-mono text-ink-muted hover:text-ink-primary hover:bg-surface-elevated"
          title="Cerrar panel lateral"
        >
          ✕
        </button>
      </div>

      {/* Píldora de Contexto UI Vivo */}
      <div className="px-3.5 py-2 bg-surface-ground border-b border-surface-border flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono">
        <span className="text-ink-secondary">
          Módulo: <strong className="text-ink-primary">{moduleLabels[uiContext?.active_module] || 'General'}</strong>
        </span>
        {selectedIncident && (
          <span className="px-2 py-0.5 rounded bg-surface-card border border-surface-border text-ink-primary font-bold">
            {selectedIncident.incident_code} • {uiContext?.active_tab || 'Detalle'}
          </span>
        )}
      </div>

      {/* Historial de Mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="p-3.5 rounded bg-surface-ground border border-surface-border text-xs text-ink-secondary leading-relaxed">
            Consulta en lenguaje natural los registros históricos (2023–2026) en tiempo real mediante SQLGlot,
            el expediente abierto en pantalla o los controles ISO/IEC 27701:2025 y normativa auxiliar ANPD.
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start w-full'}`}>
            <div className="text-[10px] font-mono text-ink-muted mb-1 px-1 flex items-center gap-1.5">
              <span>{msg.role === 'user' ? 'Operador' : 'Asistente PIMS / LangGraph'}</span>
              {msg.sql_executed && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono">
                  SQL Tiempo Real
                </span>
              )}
            </div>

            <div
              className={`p-3.5 rounded text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'chat-user-bubble rounded-br-none max-w-[380px]'
                  : 'chat-assistant-bubble rounded-bl-none max-w-[420px] w-full'
              }`}
            >
              {msg.role === 'user' ? (
                <div className="text-white whitespace-pre-wrap font-medium">{msg.content}</div>
              ) : (
                <>
                  <div
                    className="legal-markdown text-ink-primary"
                    dangerouslySetInnerHTML={window.PIMS_API.renderLegalMarkdown(msg.content)}
                  />

                  {msg.sql_executed && (
                    <div className="mt-2.5 pt-2 border-t border-surface-border">
                      <button
                        type="button"
                        onClick={() => setExpandedSqls((p) => ({ ...p, [i]: !p[i] }))}
                        className="text-[10px] font-mono text-emerald-800 hover:underline cursor-pointer"
                      >
                        {expandedSqls[i] ? '▲ Ocultar SQL ejecutado' : '▼ Ver SQL de solo lectura (SQLGlot)'}
                      </button>
                      {expandedSqls[i] && (
                        <pre className="mt-1.5 p-2 rounded bg-surface-ground border border-surface-border text-[10px] font-mono overflow-x-auto text-ink-primary">
                          {msg.sql_executed}
                        </pre>
                      )}
                    </div>
                  )}

                  {msg.trazabilidad && msg.trazabilidad.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-surface-border">
                      <button
                        type="button"
                        onClick={() => setExpandedFlows((p) => ({ ...p, [i]: !p[i] }))}
                        className="w-full flex items-center justify-between text-[11px] font-mono px-2.5 py-1.5 rounded bg-surface-ground hover:bg-surface-elevated text-ink-secondary border border-surface-border cursor-pointer"
                      >
                        <span className="inline-flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                          <strong className="text-ink-primary">Flujo de Agentes ({msg.trazabilidad.length} nodos)</strong>
                        </span>
                        <span className="text-[10px]">{expandedFlows[i] ? '▲ Ocultar' : '▼ Ver Nodos'}</span>
                      </button>

                      {expandedFlows[i] && (
                        <div className="mt-2 p-2.5 rounded bg-surface-ground border border-surface-border space-y-1.5 text-[11px] font-mono">
                          {msg.trazabilidad.map((t, tidx) => {
                            const nombreAgente = t.agente || `Nodo ${tidx + 1}`;
                            const isUnsa = nombreAgente.toLowerCase().includes('unsa') || nombreAgente.toLowerCase().includes('a2a');
                            const isConnected = t.estado === 'ok';

                            let badgeClasses = '';
                            let rowHoverClasses = '';
                            let textHoverClasses = '';
                            let dotClasses = '';
                            let tooltipText = t.detalle || t.accion || 'Ejecución completada';

                            if (isUnsa) {
                              if (isConnected) {
                                // Hover Rojo UNSA (#821417 - unsa-800) cuando conectado
                                rowHoverClasses = 'hover:bg-unsa-50 cursor-pointer';
                                badgeClasses = 'bg-unsa-100 text-unsa-900 border border-unsa-200 group-hover:bg-unsa-800 group-hover:text-white group-hover:border-unsa-900 hover:bg-unsa-800 hover:text-white hover:border-unsa-900 transition-all duration-150';
                                textHoverClasses = 'group-hover:text-unsa-900';
                                dotClasses = 'bg-unsa-700 group-hover:bg-white animate-pulse';
                                tooltipText = `Agente UNSA conectado • ${tooltipText}`;
                              } else {
                                // Hover Amarillo cuando desconectado
                                rowHoverClasses = 'hover:bg-yellow-50 cursor-pointer';
                                badgeClasses = 'bg-amber-100 text-amber-900 border border-amber-300 group-hover:bg-yellow-400 group-hover:text-yellow-950 group-hover:border-yellow-500 hover:bg-yellow-400 hover:text-yellow-950 hover:border-yellow-500 transition-all duration-150';
                                textHoverClasses = 'group-hover:text-yellow-950';
                                dotClasses = 'bg-amber-500 group-hover:bg-yellow-900';
                                tooltipText = `Agente UNSA fuera de línea • ${tooltipText}`;
                              }
                            } else if (t.estado === 'ok') {
                              rowHoverClasses = 'hover:bg-emerald-50/40';
                              badgeClasses = 'bg-emerald-100 text-emerald-900 border border-emerald-300';
                            } else {
                              rowHoverClasses = 'hover:bg-amber-50/40';
                              badgeClasses = 'bg-amber-100 text-amber-900 border border-amber-300';
                            }

                            return (
                              <div
                                key={tidx}
                                title={tooltipText}
                                className={`group flex items-start gap-1.5 py-1 px-1.5 -mx-1.5 rounded transition-colors ${rowHoverClasses} border-b border-surface-border/40 last:border-b-0`}
                              >
                                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold shrink-0 mt-0.5 inline-flex items-center ${badgeClasses}`}>
                                  {isUnsa && <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${dotClasses}`}></span>}
                                  {nombreAgente}
                                </span>
                                <span className={`text-[10px] text-ink-secondary leading-tight mt-0.5 ${textHoverClasses}`}>
                                  {t.accion || t.detalle}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ))}

        {chatLoading && (
          <div className="p-3 rounded bg-surface-ground border border-surface-border text-xs font-mono text-ink-secondary flex items-center gap-2">
            <span className="w-3.5 h-3.5 border-2 border-[var(--unsa-primary)] border-t-transparent rounded-full animate-spin"></span>
            <span>Ejecutando consulta (SQLGlot + LangGraph)...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Sugerencias rápidas */}
      <div className="p-2.5 border-t border-surface-border bg-surface-ground flex flex-wrap gap-1.5">
        {suggestions.map((sug, idx) => (
          <button
            key={idx}
            onClick={() => onSendMessage(sug)}
            disabled={chatLoading}
            className="px-2 py-1 rounded bg-surface-card hover:bg-surface-elevated text-ink-primary border border-surface-border text-[11px] transition-colors disabled:opacity-50 text-left"
          >
            {sug}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-surface-border bg-surface-sidebar flex items-center gap-2">
        <input
          type="text"
          value={chatInput}
          disabled={chatLoading}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !chatLoading && onSendMessage()}
          placeholder={chatLoading ? 'Consultando agentes...' : 'Consultar BD, incidentes o normativa ISO 27701...'}
          className="flex-1 bg-surface-card border border-surface-border rounded px-3 py-1.5 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-[var(--unsa-primary)]"
        />
        <button
          onClick={() => onSendMessage()}
          disabled={chatLoading || !chatInput.trim()}
          className="px-3.5 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] disabled:opacity-50 text-white text-xs font-semibold cursor-pointer"
        >
          Enviar
        </button>
      </div>
    </div>
  );
};
