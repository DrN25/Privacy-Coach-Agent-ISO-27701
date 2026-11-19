// ==============================================================================
// Módulos Secundarios PIMS UNSA:
// 2. Medidas Correctivas (Cl. 10.2 / D34 / D35)
// 3. Inspector SQL / PDF (DSPM -> Promover a BD)
// 4. Controles ISO/IEC 27701:2025 (78 Controles + Corpus Documental UNSA)
// 5. Responsables, Activos, Destinatarios y Configuración Institucional
// ==============================================================================

window.MedidasCorrectivasView = function MedidasCorrectivasView({
  onOpenIncident,
  incidents,
  users,
  controls,
  onRefreshAll,
  showToast,
}) {
  const { useState, useEffect, useRef } = React;
  const { MC_STATUS_MAP, apiFetch } = window.PIMS_API;
  const [items, setItems] = useState([]);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [d35Modal, setD35Modal] = useState({ open: false, markdown: '' });
  const [mcModal, setMcModal] = useState({ open: false, saving: false, data: null });
  const importD34Ref = useRef(null);

  const loadMc = async () => {
    const qs = statusFilter !== 'ALL' ? `?status=${encodeURIComponent(statusFilter)}` : '';
    const res = await fetch(`/api/corrective-actions${qs}`, { cache: 'no-store' });
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

  const openNewMcModal = () => {
    setMcModal({
      open: true,
      saving: false,
      data: {
        id: null,
        incident_id: '',
        source_type: 'AUDITORIA_INTERNA',
        iso27701_control_id: 'A.3.12',
        status: 'ABIERTA',
        due_date: '',
        action_required: true,
        nonconformity_desc: '',
        root_cause: '',
        action_to_implement: '',
        responsible_name: '',
        approved_by_name: '',
      },
    });
  };

  const handleImportD34 = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch('/api/corrective-actions/import-docx', { method: 'POST', body: fd });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.draft) {
        setMcModal({
          open: true,
          saving: false,
          data: {
            ...data.draft,
            id: null,
            incident_id: data.matched_incident ? String(data.matched_incident.id) : '',
          },
        });
        showToast(data.mensaje || 'Formulario D34 importado. Revise y guarde.', 'success');
      } else {
        showToast(data.detail || 'No se pudo importar el D34.', 'error');
      }
    } catch {
      showToast('Error de red al importar D34.', 'error');
    } finally {
      e.target.value = '';
    }
  };

  const handleSaveMcModal = async (e) => {
    e.preventDefault();
    if (!mcModal.data) return;
    setMcModal((p) => ({ ...p, saving: true }));
    try {
      const payload = {
        ...mcModal.data,
        incident_id: mcModal.data.incident_id ? parseInt(mcModal.data.incident_id, 10) : null,
      };
      const isUpdate = Boolean(mcModal.data.id);
      const url = isUpdate ? `/api/corrective-actions/${mcModal.data.id}` : '/api/corrective-actions';
      const method = isUpdate ? 'PUT' : 'POST';
      const res = await apiFetch(url, { method, body: JSON.stringify(payload) });
      const resData = await res.json().catch(() => ({}));
      if (res.ok) {
        showToast(resData.mensaje || 'Medida correctiva guardada.', 'success');
        setMcModal({ open: false, saving: false, data: null });
        await loadMc();
        onRefreshAll && onRefreshAll();
      } else {
        showToast(resData.detail || 'Error al guardar Medida Correctiva.', 'error');
      }
    } finally {
      setMcModal((p) => (p.open ? { ...p, saving: false } : p));
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
            Gestión de medidas correctivas (vinculadas o independientes Cl. 10.2), Minutas D35 (Cl. 9.3), Procedimiento MC e Informe de No Conformidades.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input ref={importD34Ref} type="file" className="hidden" accept=".docx" onChange={handleImportD34} />
          <button
            type="button"
            onClick={openNewMcModal}
            className="px-3.5 py-2 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold cursor-pointer"
          >
            + Nueva Medida 10.2
          </button>
          <button
            type="button"
            onClick={() => importD34Ref.current?.click()}
            className="px-3 py-2 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated text-ink-primary text-xs font-semibold cursor-pointer"
          >
            Importar D34 (.docx)
          </button>
          <button
            type="button"
            onClick={handleOpenD35}
            className="px-3 py-2 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated text-ink-primary text-xs font-semibold cursor-pointer"
          >
            Vista Previa D35
          </button>
          <a
            href="/api/reports/management-review-d35?format=docx"
            className="px-3 py-2 rounded bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold"
          >
            Minutas D35 (.docx)
          </a>
          <a
            href="/api/reports/corrective-procedure-docx"
            className="px-3 py-2 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated text-ink-primary text-xs font-medium"
          >
            Procedimiento MC (.docx)
          </a>
          <a
            href="/api/reports/audit-nonconformities-docx"
            className="px-3 py-2 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated text-ink-primary text-xs font-medium"
          >
            Informe NC (.docx)
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
              <th className="p-3">Origen / Control ISO</th>
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
                    <div className="font-mono text-[11px] font-semibold text-ink-primary flex flex-wrap items-center gap-1.5">
                      {mc.incident_code ? (
                        <span>{mc.incident_code}</span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-900 border border-amber-300 text-[10px]">
                          Independiente ({mc.source_type || 'Cl. 10.2'})
                        </span>
                      )}
                      <span className="text-ink-muted">({mc.iso27701_control_id || 'A.3.12'})</span>
                    </div>
                    <div className="text-ink-secondary line-clamp-1 max-w-xs">{mc.incident_title || mc.nonconformity_desc}</div>
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
                      type="button"
                      onClick={() => {
                        if (mc.incident_id) {
                          onOpenIncident(mc.incident_id, 'mc102');
                        } else {
                          setMcModal({ open: true, saving: false, data: { ...mc, incident_id: '' } });
                        }
                      }}
                      className="px-2.5 py-1 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated font-mono text-[11px] cursor-pointer"
                    >
                      Editar
                    </button>
                    <a
                      href={`/api/corrective-actions/${mc.id}/export-docx`}
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

      {/* Modal Creación / Edición MC Independiente o Importada D34 */}
      {mcModal.open && mcModal.data && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-xs" style={{ backgroundColor: 'var(--modal-overlay)' }}>
          <form onSubmit={handleSaveMcModal} className="bg-surface-card border border-surface-border rounded max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden text-xs">
            <div className="p-4 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
              <div className="font-serif font-bold text-sm text-ink-primary">
                {mcModal.data.id ? `Editar Medida Correctiva ${mcModal.data.mc_code}` : 'Registrar Medida Correctiva Cláusula 10.2 (D34)'}
              </div>
              <button type="button" onClick={() => setMcModal({ open: false, saving: false, data: null })} className="text-ink-muted hover:text-ink-primary">✕</button>
            </div>
            <div className="p-5 flex-1 overflow-y-auto space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold mb-1">Vincular a Incidente (opcional)</label>
                  <select
                    value={mcModal.data.incident_id || ''}
                    onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, incident_id: e.target.value } }))}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                  >
                    <option value="">-- Sin incidente previo (Medida independiente Cl. 10.2) --</option>
                    {(incidents || []).map((inc) => (
                      <option key={inc.id} value={inc.id}>{inc.incident_code} — {inc.title.slice(0, 50)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold mb-1">Origen de No Conformidad</label>
                  <select
                    value={mcModal.data.source_type || 'AUDITORIA_INTERNA'}
                    onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, source_type: e.target.value } }))}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                  >
                    <option value="AUDITORIA_INTERNA">Auditoría Interna (Cl. 9.2)</option>
                    <option value="REVISION_DIRECCION">Revisión por Dirección (Cl. 9.3)</option>
                    <option value="IMPORTACION_D34">Importación D34 (.docx)</option>
                    <option value="MANUAL">Registro Manual Directo</option>
                    <option value="INCIDENTE">Incidente A.3.12</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold mb-1">Control ISO 27701:2025</label>
                  <select
                    value={mcModal.data.iso27701_control_id || 'A.3.12'}
                    onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, iso27701_control_id: e.target.value } }))}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground font-mono"
                  >
                    {(controls || []).map((c) => (
                      <option key={c.id} value={c.id}>{c.id} — {c.title}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold mb-1">Estado MC</label>
                  <select
                    value={mcModal.data.status || 'ABIERTA'}
                    onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, status: e.target.value } }))}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                  >
                    {Object.keys(MC_STATUS_MAP).map((k) => (
                      <option key={k} value={k}>{MC_STATUS_MAP[k].label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold mb-1">Fecha Límite</label>
                  <input
                    type="date"
                    value={mcModal.data.due_date || ''}
                    onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, due_date: e.target.value } }))}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                  />
                </div>
              </div>
              <div>
                <label className="block font-semibold mb-1">Descripción de la no-conformidad *</label>
                <textarea
                  rows={2}
                  required
                  value={mcModal.data.nonconformity_desc || ''}
                  onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, nonconformity_desc: e.target.value } }))}
                  className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Causa raíz</label>
                <textarea
                  rows={2}
                  value={mcModal.data.root_cause || ''}
                  onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, root_cause: e.target.value } }))}
                  className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                />
              </div>
              <div>
                <label className="block font-semibold mb-1">Medida correctiva a implementar</label>
                <textarea
                  rows={2}
                  value={mcModal.data.action_to_implement || ''}
                  onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, action_to_implement: e.target.value } }))}
                  className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold mb-1">Responsable de Implementación</label>
                  <input
                    type="text"
                    value={mcModal.data.responsible_name || ''}
                    onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, responsible_name: e.target.value } }))}
                    placeholder={(users && users[0]?.full_name) || 'Responsable UNSA'}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                  />
                </div>
                <div>
                  <label className="block font-semibold mb-1">Aprobado por</label>
                  <input
                    type="text"
                    value={mcModal.data.approved_by_name || ''}
                    onChange={(e) => setMcModal((p) => ({ ...p, data: { ...p.data, approved_by_name: e.target.value } }))}
                    placeholder="Abog. Carlos Mendoza Valdivia (DPO)"
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                  />
                </div>
              </div>
            </div>
            <div className="p-3 border-t border-surface-border bg-surface-sidebar flex justify-end gap-2">
              <button type="button" onClick={() => setMcModal({ open: false, saving: false, data: null })} className="px-3.5 py-1.5 rounded border border-surface-border bg-surface-card text-ink-secondary">
                Cancelar
              </button>
              <button type="submit" disabled={mcModal.saving} className="px-4 py-1.5 rounded bg-[var(--unsa-primary)] text-white font-semibold cursor-pointer disabled:opacity-50">
                {mcModal.saving ? 'Guardando...' : 'Guardar Medida 10.2'}
              </button>
            </div>
          </form>
        </div>
      )}

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
  onOpenPromoteModal,
  onOpenExistingIncident,
  onInspectDocument,
  refreshKey,
  showToast,
}) {
  const { useState, useEffect, useRef } = React;
  const { apiFetch } = window.PIMS_API;
  const [dbView, setDbView] = useState({ archivos: [], hallazgos: [], resumen_impacto: {} });
  const [busy, setBusy] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);
  const [autoAiAfterUpload, setAutoAiAfterUpload] = useState(false);
  const [aiSummary, setAiSummary] = useState(null);
  const [draftingId, setDraftingId] = useState(null);
  const fileRef = useRef(null);

  const loadView = async () => {
    const res = await fetch('/api/database-view', { cache: 'no-store' });
    if (res.ok) setDbView(await res.json());
  };

  useEffect(() => {
    loadView();
  }, [refreshKey]);

  const handleResetInspector = async () => {
    setBusy(true);
    try {
      const res = await apiFetch('/api/reset', { method: 'POST' });
      if (res.ok) {
        setAiSummary(null);
        showToast('Bandeja del Inspector limpiada. Listo para analizar un nuevo archivo.', 'info');
        await loadView();
      }
    } finally {
      setBusy(false);
    }
  };

  const handleRunAiInspector = async (archivoId = null) => {
    setAiBusy(true);
    try {
      const qs = archivoId ? `?archivo_id=${encodeURIComponent(archivoId)}` : '';
      const res = await apiFetch(`/api/inspector/ai-analyze${qs}`, { method: 'POST' });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setAiSummary(data);
        showToast(data.mensaje || 'Análisis con Subagente IA completado.', data.ai_executed ? 'success' : 'info');
        await loadView();
      } else {
        showToast(data.detail || 'Error al ejecutar Subagente IA.', 'error');
      }
    } catch {
      showToast('Error de red al invocar Subagente IA.', 'error');
    } finally {
      setAiBusy(false);
    }
  };

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
        if (autoAiAfterUpload && data.archivo_id) {
          await handleRunAiInspector(data.archivo_id);
        }
      } else {
        showToast(data.detail || 'Formato no soportado.', 'error');
      }
    } catch {
      showToast('Error de red al subir el archivo.', 'error');
    } finally {
      setBusy(false);
      e.target.value = '';
    }
  };

  const handlePromote = async (h) => {
    setDraftingId(h.id);
    try {
      const res = await apiFetch(`/api/incidents/draft-from-finding/${h.id}`, { method: 'POST' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        showToast(data.detail || 'Error al generar borrador desde hallazgo.', 'error');
        return;
      }
      if (data.already_exists && data.incident) {
        showToast(data.mensaje || `Abriendo ${data.incident.incident_code}.`, 'info');
        onOpenExistingIncident && onOpenExistingIncident(data.incident);
        return;
      }
      if (data.draft) {
        onOpenPromoteModal && onOpenPromoteModal(data.draft, {
          findingId: h.id,
          ruleCode: h.codigo_regla,
          aiEnriched: Boolean(data.ai_enriched),
          sourceFile: h.origen_archivo,
        });
      }
    } catch {
      showToast('Error de red al preparar borrador del incidente.', 'error');
    } finally {
      setDraftingId(null);
    }
  };

  return (
    <div className="p-4 sm:p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-lg font-bold text-ink-primary">
            Inspector SQL / PDF / DOCX (DSPM + Subagente IA ➔ Registro BD)
          </h1>
          <p className="text-xs text-ink-secondary">
            Escanea esquemas SQL, documentos PDF/DOCX/MD/TXT e Informes de Auditoría para detectar brechas con reglas fijas o con el Subagente IA (78 controles).
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input ref={fileRef} type="file" className="hidden" accept=".sql,.pdf,.docx,.md,.txt" onChange={handleUpload} />
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={busy || aiBusy}
            className="px-3.5 py-2 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated text-xs font-semibold cursor-pointer disabled:opacity-50"
          >
            + Subir SQL / PDF / DOCX / TXT
          </button>
          <button
            type="button"
            onClick={() => handleRunAiInspector(null)}
            disabled={busy || aiBusy || !(dbView.archivos?.length > 0)}
            className="px-3.5 py-2 rounded bg-indigo-700 hover:bg-indigo-800 text-white text-xs font-semibold cursor-pointer disabled:opacity-40"
          >
            {aiBusy ? 'Analizando con Subagente IA...' : 'Analizar con Subagente IA (78 Controles)'}
          </button>
          <button
            type="button"
            onClick={handleLoadMockups}
            disabled={busy || aiBusy}
            className="px-4 py-2 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold cursor-pointer disabled:opacity-50"
          >
            {busy ? 'Procesando...' : 'Cargar y Auditar Corpus UNSA'}
          </button>
          {(dbView.archivos?.length > 0 || dbView.hallazgos?.length > 0) && (
            <button
              type="button"
              onClick={handleResetInspector}
              disabled={busy || aiBusy}
              className="px-3 py-2 rounded border border-surface-border bg-surface-ground hover:bg-surface-elevated text-xs text-ink-secondary cursor-pointer disabled:opacity-50"
            >
              Limpiar Inspector
            </button>
          )}
        </div>
      </div>

      <div className="px-3.5 py-2 rounded bg-surface-card border border-surface-border flex flex-wrap items-center justify-between gap-2 text-xs">
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={autoAiAfterUpload}
            onChange={(e) => setAutoAiAfterUpload(e.target.checked)}
            className="w-4 h-4 accent-[var(--unsa-primary)]"
          />
          <span>Ejecutar Subagente IA (78 controles) automáticamente al subir un nuevo archivo</span>
        </label>
        <span className="font-mono text-[11px] text-ink-muted">Detectores: Reglas R-001..R-007 + Tabla Auditoría .docx + Subagente IA</span>
      </div>

      {aiSummary && (
        <div className="p-3.5 rounded bg-indigo-50 border border-indigo-200 text-indigo-950 text-xs space-y-1">
          <div className="font-mono font-bold text-[11px]">
            Subagente IA Documental • Tipo identificado: {aiSummary.tipo_documento} ({aiSummary.hallazgos_nuevos} hallazgos nuevos)
          </div>
          <div>{aiSummary.resumen_ejecutivo}</div>
        </div>
      )}

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
              No hay hallazgos DSPM activos en el Inspector. Suba un archivo (.sql, .pdf, .md, .txt) o ejecute "Cargar y Auditar Corpus UNSA".
            </div>
          ) : (
            dbView.hallazgos.map((h) => {
              const promotedId = h.promoted_incident_id;
              const promotedCode = h.promoted_incident_code;
              const isDrafting = draftingId === h.id;
              return (
                <div key={h.id} className="p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="space-y-1 max-w-2xl">
                    <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
                      {String(h.codigo_regla || '').startsWith('IA-') ? (
                        <span className="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-900 font-bold">Subagente IA • {h.codigo_regla}</span>
                      ) : h.codigo_regla === 'AUD-NC' ? (
                        <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 font-bold">Auditoría .docx • {h.codigo_regla}</span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-900 font-bold">Regla DSPM • {h.codigo_regla}</span>
                      )}
                      <span className="px-1.5 py-0.5 rounded bg-surface-ground border border-surface-border">{h.control_iso27701}</span>
                      <span className="text-ink-muted">{h.nivel_riesgo} • {h.origen_archivo}</span>
                    </div>
                    <div className="font-semibold text-ink-primary">{h.titulo}</div>
                    <div className="text-ink-secondary">{h.descripcion}</div>
                  </div>
                  <div className="shrink-0">
                    {promotedId ? (
                      <button
                        type="button"
                        onClick={() => onOpenExistingIncident && onOpenExistingIncident({ id: promotedId, incident_code: promotedCode })}
                        className="px-3 py-1.5 rounded bg-emerald-700 hover:bg-emerald-800 text-white font-mono text-[11px] font-semibold cursor-pointer"
                      >
                        Ver {promotedCode} →
                      </button>
                    ) : (
                      <button
                        type="button"
                        disabled={draftingId !== null}
                        onClick={() => handlePromote(h)}
                        className="px-3 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold cursor-pointer disabled:opacity-50"
                      >
                        {isDrafting ? 'Autocompletando IA...' : 'Promover a Incidente BD'}
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
  const { useState, useEffect } = React;
  const [subTab, setSubTab] = useState('controls');
  const [tableFilter, setTableFilter] = useState('ALL');
  const [q, setQ] = useState('');
  const [templates, setTemplates] = useState([]);

  useEffect(() => {
    fetch('/api/templates/pims')
      .then((r) => (r.ok ? r.json() : { templates: [] }))
      .then((d) => setTemplates(d.templates || []))
      .catch(() => setTemplates([]));
  }, []);

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
        <div className="flex flex-wrap gap-1.5 text-xs font-mono">
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
          <button
            onClick={() => setSubTab('templates')}
            className={`px-3 py-1.5 rounded border cursor-pointer ${subTab === 'templates' ? 'bg-[var(--unsa-primary)] text-white border-[var(--unsa-primary)] font-bold' : 'bg-surface-card border-surface-border'}`}
          >
            Plantillas PIMS (.docx) ({templates.length})
          </button>
        </div>
      </div>

      {subTab !== 'templates' && (
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
      )}

      {subTab === 'templates' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {templates.map((tpl) => (
            <div key={tpl.id} className="p-4 rounded bg-surface-card border border-surface-border flex flex-col justify-between gap-3 text-xs">
              <div className="space-y-1">
                <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-[10px]">
                  <span className="px-1.5 py-0.5 rounded bg-rose-50 text-rose-900 border border-rose-200 font-bold">{tpl.clause}</span>
                  <span className="text-ink-muted">{tpl.origin}</span>
                </div>
                <div className="font-serif font-bold text-sm text-ink-primary">{tpl.title}</div>
                <div className="text-ink-secondary leading-relaxed">{tpl.description}</div>
              </div>
              <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-surface-border/60 font-mono text-[11px]">
                <a
                  href={`/api/templates/pims/${tpl.id}/blank`}
                  className="px-3 py-1.5 rounded border border-surface-border bg-surface-ground hover:bg-surface-elevated text-ink-primary font-semibold"
                >
                  Plantilla en Blanco (.docx)
                </a>
                {tpl.supports_export_live && tpl.live_url && (
                  <a
                    href={tpl.live_url}
                    className="px-3 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white font-semibold"
                  >
                    Generar con Datos BD (.docx)
                  </a>
                )}
                {tpl.supports_import && (
                  <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-900 border border-emerald-200 text-[10px]">
                    Admite Importación .docx
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : subTab === 'controls' ? (
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
