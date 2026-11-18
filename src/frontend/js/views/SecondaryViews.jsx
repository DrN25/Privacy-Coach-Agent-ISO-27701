// ==============================================================================
// Módulos Secundarios PIMS UNSA:
// 2. Medidas Correctivas (Cl. 10.2 / D34 / D35)
// 3. Inspector SQL / PDF (DSPM -> Promover a BD)
// 4. Controles ISO/IEC 27701:2025 (78 Controles + Corpus Documental UNSA)
// 5. Responsables, Activos, Destinatarios y Configuración Institucional
// ==============================================================================

window.MedidasCorrectivasView = function MedidasCorrectivasView({
  onOpenIncident,
  showToast,
}) {
  const { useState, useEffect } = React;
  const { MC_STATUS_MAP } = window.PIMS_API;
  const [items, setItems] = useState([]);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [d35Modal, setD35Modal] = useState({ open: false, markdown: '' });

  const loadMc = async () => {
    const qs = statusFilter !== 'ALL' ? `?status=${encodeURIComponent(statusFilter)}` : '';
    const res = await fetch(`/api/corrective-actions${qs}`);
    if (res.ok) {
      const data = await res.json();
      setItems(data.corrective_actions || []);
    }
  };

  useEffect(() => {
    loadMc();
  }, [statusFilter]);

  const handleOpenD35 = async () => {
    const res = await fetch('/api/reports/management-review-d35');
    if (res.ok) {
      const data = await res.json();
      setD35Modal({ open: true, markdown: data.markdown || '' });
    } else {
      showToast('No se pudo generar el informe D35.', 'error');
    }
  };

  return (
    <div className="p-4 sm:p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-lg font-bold text-ink-primary">
            Medidas Correctivas (Cláusula 10.2 / Formulario D34)
          </h1>
          <p className="text-xs text-ink-secondary">
            Seguimiento consolidado de causas raíz, acciones permanentes y reporte D35 para Revisión por la Dirección (Cl. 9.3).
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleOpenD35}
            className="px-3.5 py-2 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold cursor-pointer"
          >
            Vista Previa Reporte D35 (Cl. 9.3)
          </button>
          <a
            href="/api/reports/management-review-d35?format=docx"
            className="px-3.5 py-2 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated text-ink-primary text-xs font-semibold"
          >
            Descargar D35 (.docx)
          </a>
        </div>
      </div>

      {/* Filtros de estado MC */}
      <div className="flex flex-wrap gap-1.5 text-xs font-mono">
        {['ALL', 'ABIERTA', 'EN_PROGRESO', 'IMPLEMENTADA', 'VERIFICADA'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded border cursor-pointer ${
              statusFilter === st
                ? 'bg-[var(--unsa-primary)] text-white border-[var(--unsa-primary)] font-bold'
                : 'bg-surface-card text-ink-secondary border-surface-border hover:text-ink-primary'
            }`}
          >
            {st === 'ALL' ? 'Todas' : (MC_STATUS_MAP[st]?.label || st)}
          </button>
        ))}
      </div>

      {/* Tabla consolidada */}
      <div className="bg-surface-card border border-surface-border rounded overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-surface-sidebar border-b border-surface-border font-mono text-[11px] text-ink-muted">
            <tr>
              <th className="p-3">Código MC</th>
              <th className="p-3">Incidente / Control</th>
              <th className="p-3">Acción a Implementar</th>
              <th className="p-3">Responsable</th>
              <th className="p-3">Fecha Límite</th>
              <th className="p-3">Estado</th>
              <th className="p-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {items.map((mc) => {
              const st = MC_STATUS_MAP[mc.status] || MC_STATUS_MAP.ABIERTA;
              return (
                <tr key={mc.id} className="hover:bg-surface-ground">
                  <td className="p-3 font-mono font-bold text-ink-primary whitespace-nowrap">{mc.mc_code}</td>
                  <td className="p-3">
                    <div className="font-mono text-[11px] font-semibold text-ink-primary">
                      {mc.incident_code} ({mc.iso27701_control_id || 'A.3.12'})
                    </div>
                    <div className="text-ink-secondary line-clamp-1 max-w-xs">{mc.incident_title}</div>
                  </td>
                  <td className="p-3 text-ink-secondary max-w-sm">
                    <div className="line-clamp-2">{mc.action_to_implement || 'Por definir'}</div>
                  </td>
                  <td className="p-3 text-ink-primary whitespace-nowrap">{mc.responsible_name || 'N/A'}</td>
                  <td className="p-3 font-mono whitespace-nowrap">{mc.due_date || '—'}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold ${st.cls}`}>{st.label}</span>
                  </td>
                  <td className="p-3 text-right whitespace-nowrap space-x-1.5">
                    <button
                      onClick={() => onOpenIncident(mc.incident_id, 'mc102')}
                      className="px-2.5 py-1 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated font-mono text-[11px] cursor-pointer"
                    >
                      Editar
                    </button>
                    <a
                      href={`/api/incidents/${mc.incident_id}/corrective-action/export-docx`}
                      className="px-2.5 py-1 rounded bg-emerald-700 hover:bg-emerald-800 text-white font-mono text-[11px]"
                    >
                      .docx
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {d35Modal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-xs" style={{ backgroundColor: 'var(--modal-overlay)' }}>
          <div className="bg-surface-card border border-surface-border rounded max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
              <div className="font-serif font-bold text-sm text-ink-primary">
                Informe Revisión por la Dirección D35 (Cláusula 9.3 ISO/IEC 27701:2025)
              </div>
              <button onClick={() => setD35Modal({ open: false, markdown: '' })} className="text-ink-muted hover:text-ink-primary">✕</button>
            </div>
            <div
              className="p-5 flex-1 overflow-y-auto legal-markdown"
              dangerouslySetInnerHTML={window.PIMS_API.renderLegalMarkdown(d35Modal.markdown)}
            />
            <div className="p-3 border-t border-surface-border bg-surface-sidebar flex justify-end gap-2">
              <a
                href="/api/reports/management-review-d35?format=markdown"
                className="px-3.5 py-1.5 rounded border border-surface-border bg-surface-card text-xs font-semibold"
              >
                Descargar .md
              </a>
              <a
                href="/api/reports/management-review-d35?format=docx"
                className="px-3.5 py-1.5 rounded bg-[var(--unsa-primary)] text-white text-xs font-semibold"
              >
                Descargar .docx
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

window.InspectorView = function InspectorView({
  onPromotedIncident,
  onInspectDocument,
  showToast,
}) {
  const { useState, useEffect, useRef } = React;
  const { apiFetch } = window.PIMS_API;
  const [dbView, setDbView] = useState({ archivos: [], hallazgos: [], resumen_impacto: {} });
  const [busy, setBusy] = useState(false);
  const [promotedMap, setPromotedMap] = useState({});
  const fileRef = useRef(null);

  const loadView = async () => {
    const res = await fetch('/api/database-view');
    if (res.ok) setDbView(await res.json());
  };

  useEffect(() => {
    loadView();
  }, []);

  const handleLoadMockups = async () => {
    setBusy(true);
    try {
      const res = await apiFetch('/api/load-mockups', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        showToast(data.mensaje || 'Corpus cargado y auditado.', 'success');
        await loadView();
      }
    } finally {
      setBusy(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch('/api/upload', { method: 'POST', body: fd });
      const data = await res.json();
      if (res.ok) {
        await apiFetch('/api/reanalyze', { method: 'POST' });
        showToast(`Archivo '${file.name}' analizado correctamente.`, 'success');
        await loadView();
      } else {
        showToast(data.detail || 'Formato no soportado.', 'error');
      }
    } finally {
      setBusy(false);
      e.target.value = '';
    }
  };

  const handlePromote = async (findingId) => {
    const res = await apiFetch(`/api/incidents/from-finding/${findingId}`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      setPromotedMap((p) => ({ ...p, [findingId]: data.incident }));
      showToast(data.mensaje, 'success');
      onPromotedIncident && onPromotedIncident(data.incident);
    } else {
      showToast(data.detail || 'Error al promover hallazgo.', 'error');
    }
  };

  return (
    <div className="p-4 sm:p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-lg font-bold text-ink-primary">
            Inspector SQL / PDF (DSPM ➔ Registro BD)
          </h1>
          <p className="text-xs text-ink-secondary">
            Escanea esquemas SQL y reglamentos PDF/MD/TXT para detectar brechas y promoverlas a incidentes persistentes en la base de datos.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input ref={fileRef} type="file" className="hidden" accept=".sql,.pdf,.md,.txt" onChange={handleUpload} />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={busy}
            className="px-3.5 py-2 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated text-xs font-semibold cursor-pointer"
          >
            + Subir SQL / PDF
          </button>
          <button
            onClick={handleLoadMockups}
            disabled={busy}
            className="px-4 py-2 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold cursor-pointer disabled:opacity-50"
          >
            {busy ? 'Procesando...' : 'Cargar y Auditar Corpus UNSA'}
          </button>
        </div>
      </div>

      {/* Hallazgos detectados */}
      <div className="bg-surface-card border border-surface-border rounded overflow-hidden">
        <div className="p-3.5 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
          <span className="font-serif font-bold text-sm text-ink-primary">
            Hallazgos DSPM Detectados ({dbView.hallazgos?.length || 0})
          </span>
          <span className="text-xs font-mono text-ink-muted">
            Archivos indexados: {dbView.archivos?.length || 0}
          </span>
        </div>
        <div className="divide-y divide-surface-border">
          {(dbView.hallazgos || []).length === 0 ? (
            <div className="p-6 text-center text-xs text-ink-muted">
              No hay hallazgos DSPM activos en esta sesión. Suba un esquema SQL/PDF o ejecute "Cargar y Auditar Corpus UNSA".
            </div>
          ) : (
            dbView.hallazgos.map((h) => {
              const promoted = promotedMap[h.id];
              return (
                <div key={h.id} className="p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="space-y-1 max-w-2xl">
                    <div className="flex items-center gap-2 font-mono text-[11px]">
                      <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-900 font-bold">{h.codigo_regla}</span>
                      <span className="px-1.5 py-0.5 rounded bg-surface-ground border border-surface-border">{h.control_iso27701}</span>
                      <span className="text-ink-muted">{h.nivel_riesgo} • {h.origen_archivo}</span>
                    </div>
                    <div className="font-semibold text-ink-primary">{h.titulo}</div>
                    <div className="text-ink-secondary">{h.descripcion}</div>
                  </div>
                  <div className="shrink-0">
                    {promoted ? (
                      <button
                        onClick={() => onPromotedIncident(promoted, true)}
                        className="px-3 py-1.5 rounded bg-emerald-700 text-white font-mono text-[11px] font-semibold cursor-pointer"
                      >
                        Ver {promoted.incident_code} →
                      </button>
                    ) : (
                      <button
                        onClick={() => handlePromote(h.id)}
                        className="px-3 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold cursor-pointer"
                      >
                        Promover a Incidente BD
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Archivos indexados */}
      {(dbView.archivos || []).length > 0 && (
        <div className="bg-surface-card border border-surface-border rounded p-3.5 space-y-2">
          <div className="font-serif font-bold text-sm text-ink-primary">Archivos Analizados</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {dbView.archivos.map((a) => (
              <div key={a.id} className="p-2.5 rounded bg-surface-ground border border-surface-border flex items-center justify-between text-xs">
                <div>
                  <div className="font-mono font-semibold text-ink-primary">{a.nombre_archivo}</div>
                  <div className="text-[11px] text-ink-muted">{a.tipo_archivo} • {a.fecha_carga}</div>
                </div>
                <button
                  onClick={() => onInspectDocument(a.id)}
                  className="px-2.5 py-1 rounded border border-surface-border bg-surface-card text-[11px] font-mono cursor-pointer"
                >
                  Inspeccionar
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

window.ControlesIsoDocsView = function ControlesIsoDocsView({
  controls,
  documents,
  onFilterByControl,
  onInspectDocument,
  onOpenLegalModal,
}) {
  const { useState } = React;
  const [subTab, setSubTab] = useState('controls');
  const [tableFilter, setTableFilter] = useState('ALL');
  const [q, setQ] = useState('');

  const filteredControls = (controls || []).filter((c) => {
    if (tableFilter !== 'ALL' && c.table !== tableFilter) return false;
    if (!q.trim()) return true;
    const ql = q.toLowerCase();
    return c.id.toLowerCase().includes(ql) || (c.title || '').toLowerCase().includes(ql) || (c.annex_b_guidance || '').toLowerCase().includes(ql);
  });

  const filteredDocs = (documents || []).filter((d) => {
    if (!q.trim()) return true;
    const ql = q.toLowerCase();
    return (d.nombre || '').toLowerCase().includes(ql) || (d.descripcion || '').toLowerCase().includes(ql);
  });

  return (
    <div className="p-4 sm:p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-lg font-bold text-ink-primary">
            Catálogo Oficial ISO/IEC 27701:2025 & Corpus Documental UNSA
          </h1>
          <p className="text-xs text-ink-secondary">
            78 controles verificados (31 A.1 Controller, 18 A.2 Processor, 29 A.3 Seguridad) + documentos institucionales fuente.
          </p>
        </div>
        <div className="flex gap-1.5 text-xs font-mono">
          <button
            onClick={() => setSubTab('controls')}
            className={`px-3 py-1.5 rounded border cursor-pointer ${subTab === 'controls' ? 'bg-[var(--unsa-primary)] text-white border-[var(--unsa-primary)] font-bold' : 'bg-surface-card border-surface-border'}`}
          >
            78 Controles ISO 27701
          </button>
          <button
            onClick={() => setSubTab('docs')}
            className={`px-3 py-1.5 rounded border cursor-pointer ${subTab === 'docs' ? 'bg-[var(--unsa-primary)] text-white border-[var(--unsa-primary)] font-bold' : 'bg-surface-card border-surface-border'}`}
          >
            Documentos UNSA ({documents?.length || 0})
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        <input
          type="text"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar por código (A.3.12), título o descripción..."
          className="flex-1 min-w-[220px] px-3 py-1.5 rounded border border-surface-border bg-surface-card"
        />
        {subTab === 'controls' && (
          <div className="flex gap-1 font-mono">
            {['ALL', 'A.1', 'A.2', 'A.3'].map((tb) => (
              <button
                key={tb}
                onClick={() => setTableFilter(tb)}
                className={`px-3 py-1.5 rounded border cursor-pointer ${tableFilter === tb ? 'bg-[var(--unsa-primary)] text-white border-[var(--unsa-primary)] font-bold' : 'bg-surface-card border-surface-border'}`}
              >
                {tb === 'ALL' ? 'Todos (78)' : tb}
              </button>
            ))}
          </div>
        )}
      </div>

      {subTab === 'controls' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filteredControls.map((c) => (
            <div key={c.id} className="p-3.5 rounded bg-surface-card border border-surface-border flex flex-col justify-between gap-2 text-xs">
              <div>
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-mono font-bold text-ink-primary">{c.id} • {c.table}</span>
                  <div className="flex items-center gap-1.5">
                    {c.incidents_count > 0 && (
                      <button
                        onClick={() => onFilterByControl(c.id)}
                        className="px-2 py-0.5 rounded bg-rose-50 text-rose-900 border border-rose-200 font-mono text-[10px] font-bold cursor-pointer"
                      >
                        {c.incidents_count} incidente{c.incidents_count > 1 ? 's' : ''}
                      </button>
                    )}
                    <button
                      onClick={() => onOpenLegalModal('iso27701', c.id)}
                      className="px-2 py-0.5 rounded border border-surface-border bg-surface-ground font-mono text-[10px] cursor-pointer"
                    >
                      Puente Legal
                    </button>
                  </div>
                </div>
                <div className="font-serif font-bold text-sm text-ink-primary">{c.title}</div>
                <div className="text-[11px] font-mono text-ink-muted mb-1.5">{c.role} • Pág. PDF {c.pdf_page || 'ISO 27701'}</div>
                {c.annex_b_guidance && (
                  <div className="text-ink-secondary leading-relaxed">{c.annex_b_guidance}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filteredDocs.map((d, idx) => (
            <div key={idx} className="p-3.5 rounded bg-surface-card border border-surface-border flex items-center justify-between gap-3 text-xs">
              <div className="min-w-0">
                <div className="font-mono font-bold text-ink-primary truncate">{d.nombre}</div>
                <div className="text-ink-secondary line-clamp-1">{d.descripcion}</div>
              </div>
              <div className="flex items-center gap-1.5 shrink-0 font-mono text-[11px]">
                <button
                  onClick={() => onInspectDocument(d.id || d.nombre)}
                  className="px-2.5 py-1 rounded border border-surface-border bg-surface-ground cursor-pointer"
                >
                  Cláusulas
                </button>
                <a
                  href={d.raw_url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 rounded bg-[var(--unsa-primary)] text-white"
                >
                  Abrir
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

window.DirectoriosActivosView = function DirectoriosActivosView({
  users,
  assets,
  showToast,
  onConfigUpdated,
}) {
  const { useState, useEffect } = React;
  const { apiFetch } = window.PIMS_API;
  const [subTab, setSubTab] = useState('users');
  const [recipients, setRecipients] = useState([]);
  const [newRec, setNewRec] = useState({ email: '', label: '' });
  const [cfg, setCfg] = useState(null);
  const [dbInfo, setDbInfo] = useState(null);
  const [dbBusy, setDbBusy] = useState(false);

  const loadAux = async () => {
    const [rRes, cRes, dRes] = await Promise.all([
      fetch('/api/recipients?include_inactive=true'),
      fetch('/api/config'),
      fetch('/api/db/info'),
    ]);
    if (rRes.ok) setRecipients((await rRes.json()).recipients || []);
    if (cRes.ok) setCfg((await cRes.json()).config || null);
    if (dRes.ok) setDbInfo(await dRes.json());
  };

  useEffect(() => {
    loadAux();
  }, []);

  const handleAddRecipient = async (e) => {
    e.preventDefault();
    if (!newRec.email.trim()) return;
    const res = await apiFetch('/api/recipients', {
      method: 'POST',
      body: JSON.stringify(newRec),
    });
    if (res.ok) {
      setNewRec({ email: '', label: '' });
      showToast('Destinatario agregado.', 'success');
      loadAux();
    }
  };

  const handleToggleRecipient = async (rec) => {
    const res = await apiFetch(`/api/recipients/${rec.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !rec.is_active }),
    });
    if (res.ok) loadAux();
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    const res = await apiFetch('/api/config', {
      method: 'PUT',
      body: JSON.stringify({
        org_name: cfg.org_name,
        org_ruc: cfg.org_ruc,
        legal_rep_name: cfg.legal_rep_name,
        dpo_name: cfg.dpo_name,
        dpo_email: cfg.dpo_email,
        uit_value_pen: parseFloat(cfg.uit_value_pen || 5150),
      }),
    });
    if (res.ok) {
      showToast('Configuración institucional guardada.', 'success');
      onConfigUpdated && onConfigUpdated();
    }
  };

  const handleDbAction = async (endpoint) => {
    setDbBusy(true);
    try {
      const res = await apiFetch(endpoint, { method: 'POST' });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setDbInfo(data.info || null);
        showToast(data.mensaje || 'Operación de base de datos completada.', 'success');
        onConfigUpdated && onConfigUpdated();
      } else {
        showToast(data.detail || 'No se pudo completar la operación.', 'error');
      }
    } finally {
      setDbBusy(false);
    }
  };

  return (
    <div className="p-4 sm:p-5 space-y-4">
      <div>
        <h1 className="font-serif text-lg font-bold text-ink-primary">
          Responsables, Activos de Información y Configuración PIMS
        </h1>
        <p className="text-xs text-ink-secondary">
          Directorio organizacional UNSA ({users?.length || 0} empleados, {assets?.length || 0} activos, destinatarios y parámetros DPO).
        </p>
      </div>

      <div className="flex flex-wrap gap-1.5 text-xs font-mono">
        {[
          { id: 'users', label: `Responsables (${users?.length || 0})` },
          { id: 'assets', label: `Activos UNSA (${assets?.length || 0})` },
          { id: 'recipients', label: `Destinatarios (${recipients.length})` },
          { id: 'config', label: 'Configuración PIMS' },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setSubTab(t.id)}
            className={`px-3 py-1.5 rounded border cursor-pointer ${subTab === t.id ? 'bg-[var(--unsa-primary)] text-white border-[var(--unsa-primary)] font-bold' : 'bg-surface-card border-surface-border'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {subTab === 'users' && (
        <div className="bg-surface-card border border-surface-border rounded overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface-sidebar border-b border-surface-border font-mono text-[11px] text-ink-muted">
              <tr>
                <th className="p-3">ID</th>
                <th className="p-3">Nombre Completo</th>
                <th className="p-3">Cargo / Rol</th>
                <th className="p-3">Unidad Orgánica</th>
                <th className="p-3">Correo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {(users || []).map((u) => (
                <tr key={u.id} className="hover:bg-surface-ground">
                  <td className="p-3 font-mono">{u.id}</td>
                  <td className="p-3 font-semibold text-ink-primary">{u.full_name}</td>
                  <td className="p-3 text-ink-secondary">{u.position || 'Personal UNSA'}</td>
                  <td className="p-3 text-ink-secondary">{u.area || 'UNSA'}</td>
                  <td className="p-3 font-mono text-ink-muted">{u.email}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {subTab === 'assets' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {(assets || []).map((a) => (
            <div key={a.id} className="p-3.5 rounded bg-surface-card border border-surface-border text-xs space-y-1">
              <div className="flex items-center justify-between font-mono text-[11px]">
                <span className="font-bold text-ink-primary">{a.code} (id={a.id})</span>
                <span className="px-2 py-0.5 rounded bg-surface-ground border border-surface-border">{a.classification}</span>
              </div>
              <div className="font-serif font-bold text-sm text-ink-primary">{a.name}</div>
              <div className="text-ink-secondary">{a.description}</div>
              <div className="text-[11px] font-mono text-ink-muted pt-1">
                Custodio: {a.custodians} • Retención: {a.retention_period}
              </div>
            </div>
          ))}
        </div>
      )}

      {subTab === 'recipients' && (
        <div className="space-y-3">
          <form onSubmit={handleAddRecipient} className="p-3.5 rounded bg-surface-card border border-surface-border flex flex-wrap gap-2 text-xs">
            <input
              type="email"
              required
              value={newRec.email}
              onChange={(e) => setNewRec({ ...newRec, email: e.target.value })}
              placeholder="correo@unsa.edu.pe"
              className="px-3 py-1.5 rounded border border-surface-border bg-surface-ground"
            />
            <input
              type="text"
              required
              value={newRec.label}
              onChange={(e) => setNewRec({ ...newRec, label: e.target.value })}
              placeholder="Cargo o área destinataria"
              className="flex-1 min-w-[200px] px-3 py-1.5 rounded border border-surface-border bg-surface-ground"
            />
            <button type="submit" className="px-4 py-1.5 rounded bg-[var(--unsa-primary)] text-white font-semibold cursor-pointer">
              + Agregar Destinatario
            </button>
          </form>

          <div className="bg-surface-card border border-surface-border rounded divide-y divide-surface-border text-xs">
            {recipients.map((r) => (
              <div key={r.id} className="p-3 flex items-center justify-between gap-2">
                <div>
                  <div className="font-semibold text-ink-primary">{r.label}</div>
                  <div className="font-mono text-ink-muted">{r.email}</div>
                </div>
                <button
                  onClick={() => handleToggleRecipient(r)}
                  className={`px-2.5 py-1 rounded border font-mono text-[11px] cursor-pointer ${
                    r.is_active ? 'bg-emerald-50 text-emerald-900 border-emerald-300' : 'bg-surface-ground text-ink-muted border-surface-border'
                  }`}
                >
                  {r.is_active ? 'Activo' : 'Inactivo'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {subTab === 'config' && cfg && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
          <form onSubmit={handleSaveConfig} className="p-4 rounded bg-surface-card border border-surface-border space-y-3 text-xs">
            <div className="font-serif font-bold text-sm text-ink-primary">Parámetros Institucionales PIMS</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold mb-1">Entidad / Organización</label>
                <input
                  type="text"
                  value={cfg.org_name || ''}
                  onChange={(e) => setCfg({ ...cfg, org_name: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">RUC</label>
                <input
                  type="text"
                  value={cfg.org_ruc || ''}
                  onChange={(e) => setCfg({ ...cfg, org_ruc: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Representante Legal</label>
                <input
                  type="text"
                  value={cfg.legal_rep_name || ''}
                  onChange={(e) => setCfg({ ...cfg, legal_rep_name: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Oficial de Protección de Datos (DPO)</label>
                <input
                  type="text"
                  value={cfg.dpo_name || ''}
                  onChange={(e) => setCfg({ ...cfg, dpo_name: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Correo DPO</label>
                <input
                  type="email"
                  value={cfg.dpo_email || ''}
                  onChange={(e) => setCfg({ ...cfg, dpo_email: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">UIT de Referencia (S/)</label>
                <input
                  type="number"
                  value={cfg.uit_value_pen || 5150}
                  onChange={(e) => setCfg({ ...cfg, uit_value_pen: e.target.value })}
                  className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button type="submit" className="px-4 py-2 rounded bg-[var(--unsa-primary)] text-white font-semibold cursor-pointer">
                Guardar Configuración
              </button>
            </div>
          </form>

          {/* Panel de Puntos de Control (Snapshot) y Reset de Demostración */}
          <div className="p-4 rounded bg-surface-card border border-surface-border space-y-3 text-xs">
            <div>
              <div className="font-serif font-bold text-sm text-ink-primary">
                Base de Datos Única & Puntos de Control (Snapshots)
              </div>
              <p className="text-ink-secondary mt-0.5">
                Todo el sistema (Incidentes 2023–2026, Medidas 10.2, Inspector DSPM y Agente SQLGlot) opera sobre una única base SQLite local.
              </p>
            </div>

            {dbInfo && (
              <div className="p-3 rounded bg-surface-ground border border-surface-border font-mono text-[11px] space-y-1">
                <div className="truncate" title={dbInfo.db_path}><strong>Archivo BD:</strong> {dbInfo.db_path}</div>
                <div>
                  <strong>Registros activos:</strong> {dbInfo.incidents_count} incidentes • {dbInfo.corrective_actions_count} MC D34 • {dbInfo.actions_count} acciones ({dbInfo.db_size_kb} KB)
                </div>
                <div>
                  <strong>Punto de control:</strong>{' '}
                  {dbInfo.has_checkpoint ? (
                    <span className="text-emerald-700 font-bold">Guardado el {dbInfo.checkpoint_updated_at}</span>
                  ) : (
                    <span className="text-ink-muted">Aún no se ha guardado un snapshot personalizado</span>
                  )}
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 pt-1">
              <button
                type="button"
                disabled={dbBusy}
                onClick={() => handleDbAction('/api/db/checkpoint')}
                className="px-3.5 py-2 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white font-semibold cursor-pointer disabled:opacity-50"
              >
                1. Guardar Punto de Control Actual
              </button>
              <button
                type="button"
                disabled={dbBusy || !dbInfo?.has_checkpoint}
                onClick={() => handleDbAction('/api/db/restore-checkpoint')}
                className="px-3.5 py-2 rounded border border-surface-border bg-surface-ground hover:bg-surface-elevated text-ink-primary font-semibold cursor-pointer disabled:opacity-40"
              >
                2. Volver al Punto Guardado
              </button>
              <button
                type="button"
                disabled={dbBusy}
                onClick={() => handleDbAction('/api/db/reset-demo-seed')}
                className="px-3.5 py-2 rounded border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-950 font-semibold cursor-pointer disabled:opacity-50"
              >
                3. Restaurar Estado Inicial de Demo (15 incidentes)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
