// ==============================================================================
// App Shell — Agente 6: Sistema de Gestión de Incidentes, Brechas PII y MC 10.2
// Barra lateral izquierda fija (5 módulos + Asistente IA persistente + Operador)
// ==============================================================================

const { useState, useEffect, useCallback, useRef } = React;

const DEFAULT_FILTERS = {
  q: '',
  year: 'ALL',
  status: 'ALL',
  severity: '',
  classification: '',
  control_id: '',
  has_mc: '',
};

function App() {
  const [activeModule, setActiveModule] = useState('incidentes');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('pims_unsa_theme');
    return saved === 'sillar' ? 'sillar-lacre' : saved || 'sillar-lacre';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('pims_unsa_theme', theme);
  }, [theme]);

  const [actorId, setActorIdState] = useState(() => window.PIMS_API.getActorId());
  const handleSelectActor = (newId) => {
    const parsed = parseInt(newId, 10);
    setActorIdState(parsed);
    window.PIMS_API.setActorId(parsed);
  };

  // Datos compartidos
  const [incidents, setIncidents] = useState([]);
  const [kpis, setKpis] = useState({});
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const selectedIdRef = useRef(null);
  selectedIdRef.current = selectedIncident?.id || null;
  const [activeTab, setActiveTab] = useState('evaluacion');

  const [users, setUsers] = useState([]);
  const [assets, setAssets] = useState([]);
  const [controls, setControls] = useState([]);
  const [documents, setDocuments] = useState([]);

  // Modales y Drawer
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createModalPrefill, setCreateModalPrefill] = useState({ data: null, meta: null });
  const [inspectorRefreshKey, setInspectorRefreshKey] = useState(0);
  const [chatDrawerOpen, setChatDrawerOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const [legalModal, setLegalModal] = useState({ open: false, loading: false, tipo: '', data: null });
  const [inspectDocModal, setInspectDocModal] = useState({ open: false, loading: false, data: null });
  const [toast, setToast] = useState({ visible: false, message: '', type: 'info' });

  const showToast = useCallback((message, type = 'info') => {
    setToast({ visible: true, message, type });
    setTimeout(() => setToast((prev) => ({ ...prev, visible: false })), 4000);
  }, []);

  const fetchLegalReference = useCallback(async (tipo, refId) => {
    setLegalModal({ open: true, loading: true, tipo, data: null });
    try {
      const res = await fetch(`/api/legal-reference/${tipo}/${encodeURIComponent(refId)}`);
      if (res.ok) {
        setLegalModal({ open: true, loading: false, tipo, data: await res.json() });
      } else {
        showToast('Referencia normativa no encontrada.', 'error');
        setLegalModal({ open: false, loading: false, tipo: '', data: null });
      }
    } catch {
      setLegalModal({ open: false, loading: false, tipo: '', data: null });
    }
  }, [showToast]);

  useEffect(() => {
    window.fetchLegalRefGlobal = fetchLegalReference;
    window.__triggerLegalRefModal = fetchLegalReference;
    return () => {
      window.fetchLegalRefGlobal = null;
      window.__triggerLegalRefModal = null;
    };
  }, [fetchLegalReference]);

  const loadIncidentDetail = useCallback(async (id) => {
    if (!id) return null;
    try {
      const res = await fetch(`/api/incidents/${id}`, { cache: 'no-store' });
      if (res.ok) {
        const detail = await res.json();
        setSelectedIncident(detail);
        return detail;
      }
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || 'No se pudo cargar el expediente del incidente.', 'error');
    } catch {
      showToast('Error de red al cargar el expediente.', 'error');
    }
    return null;
  }, [showToast]);

  const loadIncidents = useCallback(async (overrideFilters = null) => {
    const f = overrideFilters || filters;
    const params = new URLSearchParams();
    if (f.q) params.set('q', f.q);
    if (f.year && f.year !== 'ALL') params.set('year', f.year);
    if (f.status && f.status !== 'ALL') params.set('status', f.status);
    if (f.severity) params.set('severity', f.severity);
    if (f.classification) params.set('classification', f.classification);
    if (f.control_id) params.set('control_id', f.control_id);
    if (f.has_mc) params.set('has_mc', f.has_mc);

    const res = await fetch(`/api/incidents?${params.toString()}`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      const list = data.incidents || [];
      setIncidents(list);
      setKpis(data.kpis || {});
      if (list.length > 0 && !selectedIdRef.current) {
        loadIncidentDetail(list[0].id);
      }
      return list;
    }
    return [];
  }, [filters, loadIncidentDetail]);

  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  useEffect(() => {
    Promise.all([
      fetch('/api/users').then((r) => r.ok ? r.json() : { users: [] }),
      fetch('/api/unsa-assets').then((r) => r.ok ? r.json() : { assets: [] }),
      fetch('/api/controls/iso27701').then((r) => r.ok ? r.json() : { controls: [] }),
      fetch('/api/mockups').then((r) => r.ok ? r.json() : { mockups: [] }),
    ]).then(([uData, aData, cData, dData]) => {
      setUsers(uData.users || []);
      setAssets(aData.assets || []);
      setControls(cData.controls || []);
      setDocuments(dData.mockups || []);
    });
  }, []);

  const handleInspectDocument = async (archivoIdOrName) => {
    setInspectDocModal({ open: true, loading: true, data: null });
    const res = await fetch(`/api/documents/${encodeURIComponent(archivoIdOrName)}/preview`);
    if (res.ok) {
      setInspectDocModal({ open: true, loading: false, data: await res.json() });
    } else {
      showToast('No se pudo inspeccionar el documento.', 'error');
      setInspectDocModal({ open: false, loading: false, data: null });
    }
  };

  const uiContext = {
    active_module: activeModule,
    selected_incident_id: selectedIncident?.id || null,
    selected_incident_code: selectedIncident?.incident_code || null,
    active_tab: activeModule === 'incidentes' ? activeTab : activeModule,
    active_filters: filters,
  };

  const handleSendChat = async (promptText) => {
    const texto = (promptText || chatInput).trim();
    if (!texto || chatLoading) return;
    setChatMessages((prev) => [...prev, { role: 'user', content: texto }]);
    if (!promptText) setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hallazgo_id: 0,
          incident_id: selectedIncident?.id || null,
          ui_context: uiContext,
          mensaje_usuario: texto,
          historial: chatMessages.slice(-6).map((m) => ({ role: m.role, content: m.content })),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setChatMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: data.mensaje || 'Respuesta generada.',
            sql_executed: data.sql_executed || '',
            trazabilidad: data.trazabilidad || [],
          },
        ]);
      } else {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || 'Error al consultar asistente.', 'error');
      }
    } catch {
      showToast('Error de red con el asistente.', 'error');
    } finally {
      setChatLoading(false);
    }
  };

  const navItems = [
    { id: 'incidentes', label: 'Incidentes y Brechas', tag: 'A.3.12' },
    { id: 'medidas', label: 'Medidas Correctivas', tag: 'Cl. 10.2' },
    { id: 'inspector', label: 'Inspector SQL / PDF', tag: 'DSPM' },
    { id: 'controles', label: 'Controles ISO y Docs', tag: '78 • UNSA' },
    { id: 'directorios', label: 'Responsables y Activos', tag: 'PIMS' },
  ];

  const themeOptions = [
    { id: 'sillar-lacre', label: 'Lacre' },
    { id: 'sillar-cobalto', label: 'Cobalto' },
    { id: 'sillar-terracota', label: 'Terracota' },
    { id: 'pizarra', label: 'Pizarra' },
  ];

  return (
    <div className="min-h-screen flex bg-surface-ground text-ink-primary font-sans">
      {/* Sidebar Fija Izquierda */}
      <aside className={`${mobileMenuOpen ? 'fixed inset-y-0 left-0 z-40 flex' : 'hidden lg:flex'} w-64 shrink-0 flex-col bg-surface-sidebar border-r border-surface-border lg:sticky lg:top-0 lg:h-screen`}>
        {/* Marca UNSA */}
        <div className="p-4 app-header border-b border-white/15 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-white/15 text-white font-serif font-bold text-sm flex items-center justify-center border border-white/25">
              U
            </div>
            <div>
              <div className="font-serif font-bold text-xs text-white leading-tight">UNSA • PIMS Agente 6</div>
              <div className="text-[10px] font-mono text-white/80">ISO/IEC 27701:2025</div>
            </div>
          </div>
          <button onClick={() => setMobileMenuOpen(false)} className="lg:hidden text-white text-xs">✕</button>
        </div>

        {/* Navegación 5 Módulos */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = activeModule === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveModule(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full px-3 py-2 rounded text-left text-xs flex items-center justify-between transition-colors cursor-pointer ${active
                  ? 'bg-[var(--unsa-primary)] text-white font-semibold shadow-xs'
                  : 'text-ink-primary hover:bg-surface-elevated'
                  }`}
              >
                <span>{item.label}</span>
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${active ? 'bg-white/20 text-white' : 'bg-surface-card text-ink-muted border border-surface-border'}`}>
                  {item.tag}
                </span>
              </button>
            );
          })}

          {/* Botón Persistente Asistente IA desde cualquier módulo */}
          <div className="pt-3 mt-3 border-t border-surface-border">
            <button
              onClick={() => setChatDrawerOpen((o) => !o)}
              className="w-full px-3 py-2.5 rounded border border-[var(--unsa-primary)] bg-surface-card hover:bg-surface-elevated text-ink-primary text-xs font-semibold flex items-center justify-between cursor-pointer shadow-2xs"
            >
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Asistente IA PIMS</span>
              </span>
              <span className="text-[10px] font-mono text-ink-muted">SQL • ISO</span>
            </button>
            {selectedIncident && (
              <div className="mt-1.5 px-2 text-[10px] font-mono text-ink-muted truncate">
                Contexto: {selectedIncident.incident_code}
              </div>
            )}
          </div>
        </nav>

        {/* Tema + Usuario en Sesión (Mock) */}
        <div className="p-3 border-t border-surface-border space-y-3 bg-surface-card/40 text-xs">
          <div>
            <div className="text-[10px] font-mono uppercase text-ink-muted mb-1">Paleta Institucional</div>
            <div className="grid grid-cols-4 gap-1">
              {themeOptions.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTheme(t.id)}
                  className={`py-1 rounded border text-[10px] font-mono cursor-pointer ${theme === t.id
                    ? 'bg-[var(--unsa-primary)] text-white border-[var(--unsa-primary)] font-bold'
                    : 'bg-surface-card text-ink-secondary border-surface-border'
                    }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-ink-muted mb-1">
              Usuario en sesión (Mock)
            </label>
            <select
              value={actorId}
              onChange={(e) => handleSelectActor(e.target.value)}
              className="w-full px-2 py-1.5 rounded border border-surface-border bg-surface-card text-[11px] text-ink-primary"
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} {u.id === 601 ? '(DPO)' : u.id === 604 ? '(CISO)' : ''}
                </option>
              ))}
            </select>
          </div>
        </div>
      </aside>

      {/* Contenido Principal */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Barra Móvil */}
        <div className="lg:hidden h-12 app-header px-4 flex items-center justify-between">
          <button onClick={() => setMobileMenuOpen(true)} className="text-white text-sm font-mono">☰ Menú</button>
          <span className="font-serif font-bold text-xs text-white">UNSA • PIMS Agente 6</span>
          <button onClick={() => setChatDrawerOpen(true)} className="px-2 py-1 rounded bg-white/15 text-white text-xs font-mono">
            IA SQL
          </button>
        </div>

        <main className="flex-1 overflow-y-auto">
          {activeModule === 'incidentes' && (
            <window.IncidentsView
              incidents={incidents}
              kpis={kpis}
              filters={filters}
              setFilters={setFilters}
              selectedIncident={selectedIncident}
              onSelectIncident={loadIncidentDetail}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              users={users}
              assets={assets}
              controls={controls}
              onRefreshList={loadIncidents}
              onRefreshDetail={loadIncidentDetail}
              onOpenCreateModal={() => {
                setCreateModalPrefill({ data: null, meta: null });
                setCreateModalOpen(true);
              }}
              onAskAiAboutCase={(inc) => {
                setSelectedIncident(inc);
                setChatDrawerOpen(true);
              }}
              onOpenLegalModal={fetchLegalReference}
              showToast={showToast}
            />
          )}

          {activeModule === 'medidas' && (
            <window.MedidasCorrectivasView
              onOpenIncident={(incId, tab) => {
                loadIncidentDetail(incId);
                setActiveTab(tab || 'mc102');
                setActiveModule('incidentes');
              }}
              showToast={showToast}
            />
          )}

          {activeModule === 'inspector' && (
            <window.InspectorView
              refreshKey={inspectorRefreshKey}
              onOpenPromoteModal={(draft, meta) => {
                setCreateModalPrefill({ data: draft, meta });
                setCreateModalOpen(true);
              }}
              onOpenExistingIncident={async (inc) => {
                setFilters(DEFAULT_FILTERS);
                await loadIncidents(DEFAULT_FILTERS);
                if (inc?.id) {
                  await loadIncidentDetail(inc.id);
                }
                setActiveTab('evaluacion');
                setActiveModule('incidentes');
              }}
              onInspectDocument={handleInspectDocument}
              showToast={showToast}
            />
          )}

          {activeModule === 'controles' && (
            <window.ControlesIsoDocsView
              controls={controls}
              documents={documents}
              onFilterByControl={(cid) => {
                setFilters({ ...DEFAULT_FILTERS, control_id: cid });
                setActiveModule('incidentes');
              }}
              onInspectDocument={handleInspectDocument}
              onOpenLegalModal={fetchLegalReference}
            />
          )}

          {activeModule === 'directorios' && (
            <window.DirectoriosActivosView
              users={users}
              assets={assets}
              showToast={showToast}
              onConfigUpdated={async () => {
                const list = await loadIncidents(DEFAULT_FILTERS);
                setInspectorRefreshKey((k) => k + 1);
                if (list.length > 0) {
                  await loadIncidentDetail(list[0].id);
                } else {
                  setSelectedIncident(null);
                }
              }}
            />
          )}
        </main>
      </div>

      {/* Chat Persistente */}
      <window.ChatDrawer
        open={chatDrawerOpen}
        onClose={() => setChatDrawerOpen(false)}
        uiContext={uiContext}
        selectedIncident={selectedIncident}
        messages={chatMessages}
        onSendMessage={handleSendChat}
        chatInput={chatInput}
        setChatInput={setChatInput}
        chatLoading={chatLoading}
      />

      {/* Modal Creación 3 pasos (Nuevo / Promovido DSPM + IA) */}
      <window.IncidentCreateModal
        open={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          setCreateModalPrefill({ data: null, meta: null });
        }}
        users={users}
        assets={assets}
        controls={controls}
        prefillData={createModalPrefill.data}
        prefillMeta={createModalPrefill.meta}
        onCreated={async (inc) => {
          setCreateModalPrefill({ data: null, meta: null });
          setInspectorRefreshKey((k) => k + 1);
          setFilters(DEFAULT_FILTERS);
          await loadIncidents(DEFAULT_FILTERS);
          if (inc?.id) {
            await loadIncidentDetail(inc.id);
          }
          setActiveTab('evaluacion');
          setActiveModule('incidentes');
        }}
        showToast={showToast}
      />

      {/* Modal Referencia Normativa */}
      {legalModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-xs" style={{ backgroundColor: 'var(--modal-overlay)' }}>
          <div className="bg-surface-card border border-surface-border rounded max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
              <div className="font-serif font-bold text-sm text-ink-primary">
                {legalModal.data?.titulo || 'Referencia Normativa'}
              </div>
              <button onClick={() => setLegalModal({ open: false, loading: false, tipo: '', data: null })} className="text-ink-muted hover:text-ink-primary">✕</button>
            </div>
            <div className="p-5 flex-1 overflow-y-auto space-y-3 text-xs leading-relaxed">
              {legalModal.loading ? (
                <div className="text-center font-mono text-ink-muted py-6">Cargando...</div>
              ) : (
                <>
                  {legalModal.data?.data?.annex_b_guidance && (
                    <div className="p-3 rounded bg-surface-ground border border-surface-border">
                      <div className="font-mono text-[11px] font-bold text-ink-muted uppercase mb-1">Guía Anexo B (ISO/IEC 27701:2025)</div>
                      <p className="text-ink-primary">{legalModal.data.data.annex_b_guidance}</p>
                    </div>
                  )}
                  <div className="p-3 rounded bg-amber-50 border border-amber-200 text-amber-950 whitespace-pre-line">
                    {legalModal.data?.texto_oficial || legalModal.data?.descripcion}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal Inspección Documental */}
      {inspectDocModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-xs" style={{ backgroundColor: 'var(--modal-overlay)' }}>
          <div className="bg-surface-card border border-surface-border rounded max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
              <div className="font-serif font-bold text-sm text-ink-primary">
                {inspectDocModal.data?.archivo?.nombre_archivo || 'Inspección de Documento'}
              </div>
              <button onClick={() => setInspectDocModal({ open: false, loading: false, data: null })} className="text-ink-muted hover:text-ink-primary">✕</button>
            </div>
            <div className="p-5 flex-1 overflow-y-auto space-y-3 text-xs">
              {inspectDocModal.loading ? (
                <div className="text-center font-mono text-ink-muted py-6">Analizando cláusulas y columnas AST...</div>
              ) : (
                <>
                  {inspectDocModal.data?.raw_url && (
                    <a
                      href={inspectDocModal.data.raw_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-block px-3 py-1.5 rounded bg-[var(--unsa-primary)] text-white font-semibold"
                    >
                      Abrir Archivo Nativo
                    </a>
                  )}
                  {(inspectDocModal.data?.clausulas || []).map((c, idx) => (
                    <div key={idx} className="p-3 rounded bg-surface-ground border border-surface-border">
                      <div className="font-mono font-bold text-ink-primary">{c.numero_clausula} — {c.titulo_clausula}</div>
                      <p className="text-ink-secondary mt-1">{c.texto_clausula}</p>
                    </div>
                  ))}
                  {(inspectDocModal.data?.columnas_sensibles || []).slice(0, 20).map((col, idx) => (
                    <div key={idx} className="p-2 rounded bg-surface-ground border border-surface-border font-mono text-[11px]">
                      <strong>{col.nombre_tabla}.{col.nombre_columna}</strong> • {col.categoria_sensible}
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast.visible && (
        <div className="fixed bottom-4 left-4 z-50 px-4 py-2.5 rounded bg-surface-card border border-surface-borderLight text-xs text-ink-primary shadow-xl flex items-center gap-2 font-mono">
          <span className={`w-2.5 h-2.5 rounded-full ${toast.type === 'error' ? 'bg-rose-500' : 'bg-emerald-500'}`}></span>
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
