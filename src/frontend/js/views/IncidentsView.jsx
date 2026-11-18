// ==============================================================================
// Módulo 1: Incidentes y Brechas ISO/IEC 27701:2025 (A.3.11 / A.3.12 / Cl. 10.2)
// Sin reloj de 48h en vivo, sin módulo dedicado ANPD.
// ==============================================================================

window.IncidentsView = function IncidentsView({
  incidents,
  kpis,
  filters,
  setFilters,
  selectedIncident,
  onSelectIncident,
  activeTab,
  setActiveTab,
  users,
  assets,
  controls,
  onRefreshList,
  onRefreshDetail,
  onOpenCreateModal,
  onAskAiAboutCase,
  onOpenLegalModal,
  showToast,
}) {
  const { useState, useEffect, useRef } = React;
  const { STATUS_MAP, SEVERITY_MAP, TYPE_MAP, MC_STATUS_MAP, apiFetch } = window.PIMS_API;

  const [evalForm, setEvalForm] = useState({});
  const [savingEval, setSavingEval] = useState(false);

  const [newAction, setNewAction] = useState({ action_type: 'C', responsible: '', description: '', evidence: '' });
  const [addingAction, setAddingAction] = useState(false);

  const [mcForm, setMcForm] = useState({});
  const [savingMc, setSavingMc] = useState(false);
  const [aiDraftingMc, setAiDraftingMc] = useState(false);

  const [statusModal, setStatusModal] = useState({ open: false, targetStatus: '', isReopen: false, incidentCode: '' });
  const [uploadingAtt, setUploadingAtt] = useState(false);
  const attInputRef = useRef(null);

  useEffect(() => {
    if (selectedIncident) {
      setEvalForm({
        involves_personal_data: Boolean(selectedIncident.involves_personal_data),
        incident_type: selectedIncident.incident_type || 'BF',
        severity: selectedIncident.severity || 'M',
        impact: selectedIncident.impact || 'M',
        iso27701_control_id: selectedIncident.iso27701_control_id || 'A.3.12',
        num_affected_subjects: selectedIncident.num_affected_subjects || 0,
        consequences_summary: selectedIncident.consequences_summary || '',
        data_recovered_status: selectedIncident.data_recovered_status || 'NO_APLICA',
        data_recovered_detail: selectedIncident.data_recovered_detail || '',
        anpd_notified: Boolean(selectedIncident.anpd_notified),
        anpd_notified_at: selectedIncident.anpd_notified_at || '',
        anpd_official_ref: selectedIncident.anpd_official_ref || '',
        anpd_delay_justification: selectedIncident.anpd_delay_justification || '',
        subjects_notified: Boolean(selectedIncident.subjects_notified),
        subjects_notified_at: selectedIncident.subjects_notified_at || '',
        subjects_notice_channel: selectedIncident.subjects_notice_channel || '',
      });
      const mc = selectedIncident.corrective_action || {};
      setMcForm({
        mc_code: mc.mc_code || '',
        nonconformity_desc: mc.nonconformity_desc || '',
        identified_on: mc.identified_on || selectedIncident.detection_date || '',
        identified_by_name: mc.identified_by_name || selectedIncident.reported_by || '',
        identified_signature: mc.identified_signature || '',
        root_cause: mc.root_cause || '',
        similar_mc_ref: mc.similar_mc_ref || '',
        action_required: mc.action_required === undefined ? true : Boolean(mc.action_required),
        action_to_implement: mc.action_to_implement || '',
        notify_who: mc.notify_who || '',
        approved_by_name: mc.approved_by_name || '',
        due_date: mc.due_date || '',
        responsible_name: mc.responsible_name || selectedIncident.assigned_to || '',
        implemented_on: mc.implemented_on || '',
        implemented_signature: mc.implemented_signature || '',
        effectiveness_reviewed_on: mc.effectiveness_reviewed_on || '',
        effectiveness_signature: mc.effectiveness_signature || '',
        doc_changes_required: mc.doc_changes_required || '',
        doc_changes_signature: mc.doc_changes_signature || '',
        status: mc.status || 'ABIERTA',
      });
    }
  }, [selectedIncident?.id, selectedIncident?.updated_at, selectedIncident?.corrective_action?.updated_at]);

  const handleAssignUser = async (userId) => {
    if (!selectedIncident || !userId) return;
    try {
      const res = await apiFetch(`/api/incidents/${selectedIncident.id}/assign`, {
        method: 'PATCH',
        body: JSON.stringify({ assigned_to_id: parseInt(userId, 10) }),
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.mensaje || 'Responsable asignado.', 'success');
        onRefreshDetail(selectedIncident.id);
        onRefreshList();
      } else {
        showToast(data.detail || 'Error al asignar responsable.', 'error');
      }
    } catch {
      showToast('Error al asignar responsable.', 'error');
    }
  };

  const requestStatusChange = (targetStatus) => {
    if (!selectedIncident || selectedIncident.status === targetStatus) return;
    const isReopen = selectedIncident.status === 'C' && (targetStatus === 'I' || targetStatus === 'E');
    if (isReopen || targetStatus === 'C') {
      setStatusModal({
        open: true,
        targetStatus,
        isReopen,
        incidentCode: selectedIncident.incident_code,
      });
    } else {
      executeStatusChange(targetStatus, '');
    }
  };

  const executeStatusChange = async (targetStatus, reason) => {
    try {
      const res = await apiFetch(`/api/incidents/${selectedIncident.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: targetStatus, reason }),
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.mensaje || 'Estado actualizado.', 'success');
        setStatusModal({ open: false, targetStatus: '', isReopen: false, incidentCode: '' });
        onRefreshDetail(selectedIncident.id);
        onRefreshList();
      } else {
        showToast(data.detail || 'No se pudo cambiar el estado.', 'error');
      }
    } catch {
      showToast('Error al cambiar el estado.', 'error');
    }
  };

  const handleSaveEvaluation = async (e) => {
    e.preventDefault();
    setSavingEval(true);
    try {
      const res = await apiFetch(`/api/incidents/${selectedIncident.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          ...evalForm,
          num_affected_subjects: parseInt(evalForm.num_affected_subjects || 0, 10),
        }),
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Evaluación B.3.12 guardada.', 'success');
        onRefreshDetail(selectedIncident.id);
        onRefreshList();
      } else {
        showToast(data.detail || 'Error al guardar evaluación.', 'error');
      }
    } finally {
      setSavingEval(false);
    }
  };

  const handleAddAction = async (e) => {
    e.preventDefault();
    if (!newAction.description.trim()) return;
    setAddingAction(true);
    try {
      const res = await apiFetch(`/api/incidents/${selectedIncident.id}/actions`, {
        method: 'POST',
        body: JSON.stringify(newAction),
      });
      if (res.ok) {
        showToast('Acción A.3.12 registrada.', 'success');
        setNewAction({ action_type: 'C', responsible: '', description: '', evidence: '' });
        onRefreshDetail(selectedIncident.id);
        onRefreshList();
      }
    } finally {
      setAddingAction(false);
    }
  };

  const handleSaveMc = async (e) => {
    e.preventDefault();
    setSavingMc(true);
    try {
      const res = await apiFetch(`/api/incidents/${selectedIncident.id}/corrective-action`, {
        method: 'PUT',
        body: JSON.stringify(mcForm),
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.mensaje || 'Medida correctiva 10.2 guardada.', 'success');
        onRefreshDetail(selectedIncident.id);
        onRefreshList();
      } else {
        showToast(data.detail || 'Error al guardar Medida Correctiva.', 'error');
      }
    } finally {
      setSavingMc(false);
    }
  };

  const handleAiDraftMc = async () => {
    setAiDraftingMc(true);
    try {
      const res = await apiFetch(`/api/incidents/${selectedIncident.id}/corrective-action/ai-draft`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setMcForm((prev) => ({ ...prev, ...(data.draft || {}) }));
        showToast('Borrador Cláusula 10.2 generado. Revise y guarde.', 'success');
      }
    } finally {
      setAiDraftingMc(false);
    }
  };

  const handleUploadAttachment = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedIncident) return;
    setUploadingAtt(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await apiFetch(`/api/incidents/${selectedIncident.id}/attachments`, {
        method: 'POST',
        body: fd,
      });
      if (res.ok) {
        showToast(`Evidencia '${file.name}' adjuntada.`, 'success');
        onRefreshDetail(selectedIncident.id);
      } else {
        showToast('Error al subir evidencia.', 'error');
      }
    } finally {
      setUploadingAtt(false);
      e.target.value = '';
    }
  };

  const tabs = [
    { id: 'evaluacion', label: '1. Evaluación B.3.12' },
    { id: 'acciones', label: `2. Acciones (${selectedIncident?.actions?.length || 0})` },
    { id: 'mc102', label: '3. Medida 10.2' },
    { id: 'evidencias', label: `4. Evidencias (${selectedIncident?.attachments?.length || 0})` },
  ];

  return (
    <div className="p-4 sm:p-5 space-y-4">
      {/* Cabecera módulo + botón crear */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-lg font-bold text-ink-primary">
            Gestión de Incidentes de Seguridad y Brechas PII
          </h1>
          <p className="text-xs text-ink-secondary">
            ISO/IEC 27701:2025 Cláusula 8.1 • Controles A.3.11 / A.3.12 (B.3.12) • Registro histórico 2023–2026
          </p>
        </div>
        <button
          onClick={onOpenCreateModal}
          className="px-4 py-2 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold shadow-xs cursor-pointer"
        >
          + Registrar Incidente
        </button>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-3.5 rounded border bg-surface-card border-surface-border">
          <div className="text-[11px] font-mono text-ink-muted uppercase">Incidentes Abiertos</div>
          <div className="text-2xl font-bold font-mono text-ink-primary tabular-nums mt-0.5">
            {kpis?.abiertos ?? 0}
          </div>
          <div className="text-[11px] text-ink-secondary mt-0.5">
            I: {kpis?.en_investigacion ?? 0} • E: {kpis?.en_mitigacion ?? 0} • Cerrados: {kpis?.cerrados ?? 0}
          </div>
        </div>

        <div className="p-3.5 rounded kpi-card-multa">
          <div className="text-[11px] font-mono text-ink-muted uppercase">Críticos Sin Cerrar</div>
          <div className="text-2xl font-bold font-mono kpi-num tabular-nums mt-0.5">
            {kpis?.criticos_abiertos ?? 0}
          </div>
          <div className="text-[11px] text-ink-secondary mt-0.5">Severidad Crítica (I / E)</div>
        </div>

        <div className="p-3.5 rounded kpi-card-titulares">
          <div className="text-[11px] font-mono text-ink-muted uppercase">Brechas PII vs Técnicos</div>
          <div className="text-2xl font-bold font-mono kpi-num tabular-nums mt-0.5">
            {kpis?.brechas_pii ?? 0} <span className="text-sm font-normal text-ink-muted">/ {kpis?.incidentes_tecnicos ?? 0} IT</span>
          </div>
          <div className="text-[11px] text-ink-secondary mt-0.5">Triaje B.3.12 Note 1</div>
        </div>

        <div className="p-3.5 rounded kpi-card-anpd">
          <div className="text-[11px] font-mono text-ink-muted uppercase">Medidas Correctivas 10.2</div>
          <div className="text-2xl font-bold font-mono kpi-num tabular-nums mt-0.5">
            {kpis?.mc_pendientes ?? 0}
          </div>
          <div className="text-[11px] text-ink-secondary mt-0.5">
            Pendientes ({kpis?.mc_vencidas ?? 0} con fecha vencida)
          </div>
        </div>
      </div>

      {/* Barra de Filtros Compacta */}
      <div className="p-3 rounded bg-surface-card border border-surface-border flex flex-wrap items-center gap-2 text-xs">
        <input
          type="text"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          placeholder="Buscar código, título, sistema, responsable..."
          className="flex-1 min-w-[200px] px-3 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
        />
        <select
          value={filters.year}
          onChange={(e) => setFilters({ ...filters, year: e.target.value })}
          className="px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary font-mono"
        >
          <option value="ALL">Año: Todos</option>
          <option value="2026">2026</option>
          <option value="2025">2025</option>
          <option value="2024">2024</option>
          <option value="2023">2023</option>
        </select>
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
        >
          <option value="ALL">Estado: Todos</option>
          <option value="OPEN">Abiertos (I + E)</option>
          <option value="I">En Investigación (I)</option>
          <option value="E">En Mitigación (E)</option>
          <option value="C">Cerrado (C)</option>
        </select>
        <select
          value={filters.severity}
          onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
          className="px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
        >
          <option value="">Severidad: Todas</option>
          <option value="C">Crítico</option>
          <option value="A">Alto</option>
          <option value="M">Medio</option>
          <option value="B">Bajo</option>
        </select>
        <select
          value={filters.classification}
          onChange={(e) => setFilters({ ...filters, classification: e.target.value })}
          className="px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
        >
          <option value="">Tipo: Todos</option>
          <option value="PII_BREACH">Brecha PII (BF/BI/BD)</option>
          <option value="PI">No Conformidad (PI)</option>
          <option value="TECH">Técnico sin PII (IT)</option>
        </select>
        {(filters.q || filters.year !== 'ALL' || filters.status !== 'ALL' || filters.severity || filters.classification || filters.control_id) && (
          <button
            onClick={() => setFilters({ q: '', year: 'ALL', status: 'ALL', severity: '', classification: '', control_id: '' })}
            className="px-2.5 py-1.5 rounded border border-surface-border text-ink-secondary hover:text-ink-primary"
          >
            Limpiar
          </button>
        )}
      </div>

      {/* Master-Detail */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-start">
        {/* Lista Maestra (Izquierda) */}
        <div className="xl:col-span-4 space-y-2 max-h-[72vh] overflow-y-auto pr-1">
          {incidents.length === 0 ? (
            <div className="p-6 rounded bg-surface-card border border-surface-border text-center text-xs text-ink-muted">
              No hay incidentes que coincidan con los filtros aplicados.
            </div>
          ) : (
            incidents.map((inc) => {
              const active = selectedIncident?.id === inc.id;
              const st = STATUS_MAP[inc.status] || STATUS_MAP.I;
              const sv = SEVERITY_MAP[inc.severity] || SEVERITY_MAP.M;
              return (
                <button
                  key={inc.id}
                  onClick={() => onSelectIncident(inc.id)}
                  className={`w-full text-left p-3 rounded border transition-all cursor-pointer ${
                    active
                      ? 'bg-[var(--active-card-bg)] border-[var(--active-card-border)] shadow-xs'
                      : 'bg-surface-card border-surface-border hover:border-surface-borderLight'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="font-mono text-[11px] font-bold text-ink-primary">{inc.incident_code}</span>
                    <div className="flex items-center gap-1">
                      <span className={`px-1.5 py-0.5 rounded border text-[10px] font-mono font-bold ${sv.cls}`}>
                        {sv.label}
                      </span>
                      <span className={`px-1.5 py-0.5 rounded border text-[10px] font-mono font-bold ${st.cls}`}>
                        {st.short}
                      </span>
                    </div>
                  </div>
                  <div className="text-xs font-semibold text-ink-primary line-clamp-2 leading-snug mb-1.5">
                    {inc.title}
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-1 text-[10px] font-mono text-ink-muted">
                    <span>{inc.iso27701_control_id} • {inc.involves_personal_data ? inc.incident_type : 'IT (Sin PII)'}</span>
                    <span className="truncate max-w-[160px]">{inc.assigned_to || 'Sin asignar'}</span>
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Expediente Detalle (Derecha) */}
        <div className="xl:col-span-8 bg-surface-card border border-surface-border rounded overflow-hidden">
          {!selectedIncident ? (
            <div className="p-10 text-center text-xs text-ink-muted">
              Seleccione un incidente de la lista para ver su expediente completo.
            </div>
          ) : (
            <div>
              {/* Cabecera del Expediente */}
              <div className="p-4 border-b border-surface-border bg-surface-sidebar space-y-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="font-mono text-xs font-bold text-ink-primary">{selectedIncident.incident_code}</span>
                      <button
                        type="button"
                        onClick={() => onOpenLegalModal('iso27701', selectedIncident.iso27701_control_id)}
                        className="px-2 py-0.5 rounded bg-rose-50 hover:bg-rose-100 text-rose-900 border border-rose-300 text-[11px] font-mono font-semibold cursor-pointer"
                        title="Ver detalle del control ISO/IEC 27701:2025"
                      >
                        ISO 27701 {selectedIncident.iso27701_control_id}
                      </button>
                      <span className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold ${(TYPE_MAP[selectedIncident.incident_type] || TYPE_MAP.BF).cls}`}>
                        {(TYPE_MAP[selectedIncident.incident_type] || TYPE_MAP.BF).label}
                      </span>
                    </div>
                    <h2 className="font-serif font-bold text-base text-ink-primary leading-snug">
                      {selectedIncident.title}
                    </h2>
                    <div className="text-[11px] font-mono text-ink-muted mt-1">
                      Detección: {selectedIncident.detection_date} • Activo: {selectedIncident.compromised_system || 'N/A'}
                      {selectedIncident.resolved_date ? ` • Cerrado el: ${selectedIncident.resolved_date}` : ''}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <button
                      onClick={() => onAskAiAboutCase(selectedIncident, activeTab)}
                      className="px-3 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold cursor-pointer"
                    >
                      Consultar IA sobre este caso
                    </button>
                    <a
                      href={`/api/incidents/${selectedIncident.id}/export-dictamen`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-3 py-1.5 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated text-ink-primary text-xs font-medium"
                    >
                      Exportar Ficha
                    </a>
                  </div>
                </div>

                {/* Asignación y Transición de Estado */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-surface-border/70 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-ink-muted">Responsable:</span>
                    <select
                      value={(users.find((u) => u.full_name === selectedIncident.assigned_to)?.id) || ''}
                      onChange={(e) => handleAssignUser(e.target.value)}
                      className="px-2.5 py-1 rounded border border-surface-border bg-surface-card text-ink-primary text-xs"
                    >
                      <option value="">{selectedIncident.assigned_to || 'Seleccionar...'}</option>
                      {users.map((u) => (
                        <option key={u.id} value={u.id}>{u.full_name} ({u.area})</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] font-mono text-ink-muted mr-1">Estado:</span>
                    {['I', 'E', 'C'].map((stKey) => {
                      const active = selectedIncident.status === stKey;
                      return (
                        <button
                          key={stKey}
                          type="button"
                          onClick={() => requestStatusChange(stKey)}
                          className={`px-2.5 py-1 rounded border text-[11px] font-mono font-semibold cursor-pointer transition-colors ${
                            active
                              ? 'bg-[var(--unsa-primary)] text-white border-[var(--unsa-primary)]'
                              : 'bg-surface-card text-ink-secondary border-surface-border hover:text-ink-primary'
                          }`}
                        >
                          {STATUS_MAP[stKey].label} ({stKey})
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Pestañas del Expediente */}
              <div className="flex overflow-x-auto border-b border-surface-border bg-surface-ground text-xs font-mono">
                {tabs.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setActiveTab(t.id)}
                    className={`px-4 py-2.5 whitespace-nowrap border-b-2 transition-colors cursor-pointer ${
                      activeTab === t.id
                        ? 'border-[var(--unsa-primary)] text-ink-primary font-bold bg-surface-card'
                        : 'border-transparent text-ink-muted hover:text-ink-primary'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              {/* Contenido por Pestaña */}
              <div className="p-4 sm:p-5 text-xs">
                {activeTab === 'evaluacion' && (
                  <form onSubmit={handleSaveEvaluation} className="space-y-4">
                    <div className="p-3 rounded bg-surface-ground border border-surface-border text-ink-secondary leading-relaxed">
                      <strong className="text-ink-primary block mb-1">Hechos / Descripción:</strong>
                      {selectedIncident.description}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                      <div>
                        <label className="block font-semibold mb-1">Afecta PII (B.3.12)</label>
                        <select
                          value={evalForm.involves_personal_data ? '1' : '0'}
                          onChange={(e) => setEvalForm({ ...evalForm, involves_personal_data: e.target.value === '1' })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        >
                          <option value="1">Sí — Involucra PII</option>
                          <option value="0">No — Incidente Técnico</option>
                        </select>
                      </div>
                      <div>
                        <label className="block font-semibold mb-1">Tipo</label>
                        <select
                          value={evalForm.incident_type || 'BF'}
                          onChange={(e) => setEvalForm({ ...evalForm, incident_type: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        >
                          <option value="BF">Brecha Confidencialidad (BF)</option>
                          <option value="BI">Brecha Integridad (BI)</option>
                          <option value="BD">Brecha Disponibilidad (BD)</option>
                          <option value="PI">No Conformidad Principios (PI)</option>
                          <option value="IT">Incidente Técnico sin PII (IT)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block font-semibold mb-1">Severidad / Impacto</label>
                        <select
                          value={evalForm.severity || 'M'}
                          onChange={(e) => setEvalForm({ ...evalForm, severity: e.target.value, impact: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        >
                          <option value="C">Crítico (C)</option>
                          <option value="A">Alto (A)</option>
                          <option value="M">Medio (M)</option>
                          <option value="B">Bajo (B)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block font-semibold mb-1">Titulares Afectados</label>
                        <input
                          type="number"
                          min="0"
                          value={evalForm.num_affected_subjects ?? 0}
                          onChange={(e) => setEvalForm({ ...evalForm, num_affected_subjects: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block font-semibold mb-1">Control ISO/IEC 27701:2025</label>
                        <select
                          value={evalForm.iso27701_control_id || 'A.3.12'}
                          onChange={(e) => setEvalForm({ ...evalForm, iso27701_control_id: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground font-mono"
                        >
                          {controls.map((c) => (
                            <option key={c.id} value={c.id}>{c.id} — {c.title}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block font-semibold mb-1">Estado Recuperación de Datos (B.3.12)</label>
                        <select
                          value={evalForm.data_recovered_status || 'NO_APLICA'}
                          onChange={(e) => setEvalForm({ ...evalForm, data_recovered_status: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        >
                          <option value="RECUPERADO_TOTAL">Recuperado Totalmente</option>
                          <option value="RECUPERADO_PARCIAL">Recuperado Parcialmente</option>
                          <option value="NO_RECUPERADO">No Recuperado / Expuesto</option>
                          <option value="NO_APLICA">No Aplica</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block font-semibold mb-1">Consecuencias de la Brecha (B.3.12)</label>
                        <textarea
                          rows={2}
                          value={evalForm.consequences_summary || ''}
                          onChange={(e) => setEvalForm({ ...evalForm, consequences_summary: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                      <div>
                        <label className="block font-semibold mb-1">Detalle de Datos Recuperados / Contención</label>
                        <textarea
                          rows={2}
                          value={evalForm.data_recovered_detail || ''}
                          onChange={(e) => setEvalForm({ ...evalForm, data_recovered_detail: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                    </div>

                    {/* Registro Documental de Notificaciones (Sin Reloj 48h) */}
                    <div className="p-3.5 rounded bg-surface-ground border border-surface-border space-y-3">
                      <div className="font-mono font-bold text-[11px] uppercase text-ink-secondary">
                        Registro Documental de Comunicaciones (ISO/IEC 27701:2025 B.3.12)
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={Boolean(evalForm.anpd_notified)}
                            onChange={(e) => setEvalForm({ ...evalForm, anpd_notified: e.target.checked })}
                            className="w-4 h-4 accent-[var(--unsa-primary)]"
                          />
                          <span>Autoridad notificada (ANPD)</span>
                        </label>
                        <div>
                          <label className="block text-[11px] text-ink-muted mb-1">Fecha / Hora de Oficio</label>
                          <input
                            type="text"
                            value={evalForm.anpd_notified_at || ''}
                            onChange={(e) => setEvalForm({ ...evalForm, anpd_notified_at: e.target.value })}
                            placeholder="YYYY-MM-DD HH:MM"
                            className="w-full px-2.5 py-1 rounded border border-surface-border bg-surface-card"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] text-ink-muted mb-1">Nro. Oficio / Expediente</label>
                          <input
                            type="text"
                            value={evalForm.anpd_official_ref || ''}
                            onChange={(e) => setEvalForm({ ...evalForm, anpd_official_ref: e.target.value })}
                            placeholder="Oficio N° ..."
                            className="w-full px-2.5 py-1 rounded border border-surface-border bg-surface-card"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-[11px] text-ink-muted mb-1">Justificación / Nota de Comunicación</label>
                        <input
                          type="text"
                          value={evalForm.anpd_delay_justification || ''}
                          onChange={(e) => setEvalForm({ ...evalForm, anpd_delay_justification: e.target.value })}
                          placeholder="Registro documental si hubo demora o motivo de no aplicabilidad..."
                          className="w-full px-2.5 py-1 rounded border border-surface-border bg-surface-card"
                        />
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end pt-1 border-t border-surface-border/60">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={Boolean(evalForm.subjects_notified)}
                            onChange={(e) => setEvalForm({ ...evalForm, subjects_notified: e.target.checked })}
                            className="w-4 h-4 accent-[var(--unsa-primary)]"
                          />
                          <span>Titulares comunicados</span>
                        </label>
                        <div>
                          <label className="block text-[11px] text-ink-muted mb-1">Fecha comunicación titulares</label>
                          <input
                            type="text"
                            value={evalForm.subjects_notified_at || ''}
                            onChange={(e) => setEvalForm({ ...evalForm, subjects_notified_at: e.target.value })}
                            className="w-full px-2.5 py-1 rounded border border-surface-border bg-surface-card"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] text-ink-muted mb-1">Canal empleado</label>
                          <input
                            type="text"
                            value={evalForm.subjects_notice_channel || ''}
                            onChange={(e) => setEvalForm({ ...evalForm, subjects_notice_channel: e.target.value })}
                            placeholder="Correo, comunicado oficial..."
                            className="w-full px-2.5 py-1 rounded border border-surface-border bg-surface-card"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={savingEval}
                        className="px-4 py-2 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white font-semibold cursor-pointer disabled:opacity-50"
                      >
                        {savingEval ? 'Guardando...' : 'Guardar Evaluación B.3.12'}
                      </button>
                    </div>
                  </form>
                )}

                {activeTab === 'acciones' && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      {(selectedIncident.actions || []).length === 0 ? (
                        <div className="p-4 rounded bg-amber-50 border border-amber-200 text-amber-900">
                          Aún no existen acciones registradas. Registre al menos una acción de Contención (C), Remediación (R) o Mitigación (M) antes de poder cerrar el incidente.
                        </div>
                      ) : (
                        selectedIncident.actions.map((a) => (
                          <div key={a.id} className="p-3 rounded border border-surface-border bg-surface-ground flex items-start justify-between gap-3">
                            <div>
                              <div className="flex items-center gap-2 font-mono text-[11px] mb-1">
                                <span className="px-1.5 py-0.5 rounded bg-surface-card border border-surface-border font-bold">
                                  {a.action_type === 'C' ? 'Contención (C)' : a.action_type === 'R' ? 'Remediación (R)' : 'Mitigación (M)'}
                                </span>
                                <span className="text-ink-muted">{a.action_date} • {a.responsible}</span>
                              </div>
                              <div className="text-ink-primary">{a.description}</div>
                              {a.evidence && <div className="text-[11px] font-mono text-ink-muted mt-1">Evidencia: {a.evidence}</div>}
                            </div>
                          </div>
                        ))
                      )}
                    </div>

                    {/* Agregar acción */}
                    <form onSubmit={handleAddAction} className="p-3.5 rounded border border-surface-border bg-surface-card space-y-3">
                      <div className="font-serif font-bold text-ink-primary">Registrar Nueva Acción (A.3.12)</div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <select
                          value={newAction.action_type}
                          onChange={(e) => setNewAction({ ...newAction, action_type: e.target.value })}
                          className="px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        >
                          <option value="C">Contención (C)</option>
                          <option value="R">Remediación Técnica/Legal (R)</option>
                          <option value="M">Mitigación / Organizativa (M)</option>
                        </select>
                        <input
                          type="text"
                          value={newAction.responsible}
                          onChange={(e) => setNewAction({ ...newAction, responsible: e.target.value })}
                          placeholder="Responsable (opcional, toma usuario en sesión)"
                          className="px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                      <textarea
                        rows={2}
                        required
                        value={newAction.description}
                        onChange={(e) => setNewAction({ ...newAction, description: e.target.value })}
                        placeholder="Descripción detallada de la acción ejecutada..."
                        className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                      />
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <input
                          type="text"
                          value={newAction.evidence}
                          onChange={(e) => setNewAction({ ...newAction, evidence: e.target.value })}
                          placeholder="Evidencia o ticket (ej. Commit, Log Fortinet, Oficio)"
                          className="flex-1 px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                        <button
                          type="submit"
                          disabled={addingAction}
                          className="px-4 py-1.5 rounded bg-[var(--unsa-primary)] text-white font-semibold cursor-pointer"
                        >
                          {addingAction ? 'Agregando...' : '+ Agregar Acción'}
                        </button>
                      </div>
                    </form>

                    {/* Logs técnicos disparadores (core_securitylog) */}
                    {(selectedIncident.security_logs || []).length > 0 && (
                      <div className="space-y-1.5 pt-2 border-t border-surface-border">
                        <div className="font-mono font-bold text-[11px] text-ink-muted uppercase">
                          Trazas Técnicas Asociadas al Activo (core_securitylog)
                        </div>
                        {selectedIncident.security_logs.map((log) => (
                          <div key={log.id} className="p-2.5 rounded bg-surface-ground border border-surface-border font-mono text-[11px] flex flex-wrap justify-between gap-2">
                            <span><strong>{log.action}</strong> • {log.module} ({log.username})</span>
                            <span className="text-ink-muted">{log.ip_address} • {log.created_at}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'mc102' && (
                  <form onSubmit={handleSaveMc} className="space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-surface-border">
                      <div>
                        <span className="font-serif font-bold text-sm text-ink-primary">
                          Formulario D34 — Medida Correctiva Cláusula 10.2
                        </span>
                        <span className="ml-2 font-mono text-xs text-ink-muted">
                          {mcForm.mc_code || 'Nuevo borrador'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={handleAiDraftMc}
                          disabled={aiDraftingMc}
                          className="px-3 py-1.5 rounded border border-surface-border bg-surface-ground hover:bg-surface-elevated text-ink-primary font-semibold cursor-pointer"
                        >
                          {aiDraftingMc ? 'Redactando...' : 'Autocompletar con IA'}
                        </button>
                        <a
                          href={`/api/incidents/${selectedIncident.id}/corrective-action/export-docx`}
                          className="px-3 py-1.5 rounded bg-emerald-700 hover:bg-emerald-800 text-white font-semibold"
                        >
                          Exportar .docx (D34)
                        </a>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block font-semibold mb-1">Estado MC</label>
                        <select
                          value={mcForm.status || 'ABIERTA'}
                          onChange={(e) => setMcForm({ ...mcForm, status: e.target.value })}
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
                          value={mcForm.due_date || ''}
                          onChange={(e) => setMcForm({ ...mcForm, due_date: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                      <div className="flex items-end pb-1.5">
                        <label className="flex items-center gap-2 cursor-pointer font-semibold">
                          <input
                            type="checkbox"
                            checked={Boolean(mcForm.action_required)}
                            onChange={(e) => setMcForm({ ...mcForm, action_required: e.target.checked })}
                            className="w-4 h-4 accent-[var(--unsa-primary)]"
                          />
                          <span>¿Es necesario tomar medidas? SÍ</span>
                        </label>
                      </div>
                    </div>

                    <div>
                      <label className="block font-semibold mb-1">1. Descripción de la no-conformidad</label>
                      <textarea
                        rows={2}
                        value={mcForm.nonconformity_desc || ''}
                        onChange={(e) => setMcForm({ ...mcForm, nonconformity_desc: e.target.value })}
                        className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold mb-1">3. Causa raíz de la no-conformidad</label>
                      <textarea
                        rows={2}
                        value={mcForm.root_cause || ''}
                        onChange={(e) => setMcForm({ ...mcForm, root_cause: e.target.value })}
                        className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold mb-1">6. Medida correctiva a implementar</label>
                      <textarea
                        rows={3}
                        value={mcForm.action_to_implement || ''}
                        onChange={(e) => setMcForm({ ...mcForm, action_to_implement: e.target.value })}
                        className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block font-semibold mb-1">Responsable Implementación</label>
                        <input
                          type="text"
                          value={mcForm.responsible_name || ''}
                          onChange={(e) => setMcForm({ ...mcForm, responsible_name: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                      <div>
                        <label className="block font-semibold mb-1">Aprobado por</label>
                        <input
                          type="text"
                          value={mcForm.approved_by_name || ''}
                          onChange={(e) => setMcForm({ ...mcForm, approved_by_name: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                      <div>
                        <label className="block font-semibold mb-1">¿Quién debe estar informado?</label>
                        <input
                          type="text"
                          value={mcForm.notify_who || ''}
                          onChange={(e) => setMcForm({ ...mcForm, notify_who: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block font-semibold mb-1">Implementada el</label>
                        <input
                          type="date"
                          value={mcForm.implemented_on || ''}
                          onChange={(e) => setMcForm({ ...mcForm, implemented_on: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                      <div>
                        <label className="block font-semibold mb-1">Efectividad revisada el</label>
                        <input
                          type="date"
                          value={mcForm.effectiveness_reviewed_on || ''}
                          onChange={(e) => setMcForm({ ...mcForm, effectiveness_reviewed_on: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                      <div>
                        <label className="block font-semibold mb-1">Cambios al documento PIMS</label>
                        <input
                          type="text"
                          value={mcForm.doc_changes_required || ''}
                          onChange={(e) => setMcForm({ ...mcForm, doc_changes_required: e.target.value })}
                          className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end pt-2">
                      <button
                        type="submit"
                        disabled={savingMc}
                        className="px-4 py-2 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white font-semibold cursor-pointer disabled:opacity-50"
                      >
                        {savingMc ? 'Guardando...' : 'Guardar Medida Correctiva 10.2'}
                      </button>
                    </div>
                  </form>
                )}

                {activeTab === 'evidencias' && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="font-serif font-bold text-ink-primary">Evidencias Adjuntas (A.3.14)</div>
                      <div>
                        <input ref={attInputRef} type="file" className="hidden" onChange={handleUploadAttachment} />
                        <button
                          type="button"
                          onClick={() => attInputRef.current?.click()}
                          disabled={uploadingAtt}
                          className="px-3 py-1.5 rounded bg-[var(--unsa-primary)] text-white font-semibold cursor-pointer"
                        >
                          {uploadingAtt ? 'Subiendo...' : '+ Adjuntar Evidencia'}
                        </button>
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      {(selectedIncident.attachments || []).map((att) => (
                        <div key={att.id} className="p-2.5 rounded bg-surface-ground border border-surface-border flex items-center justify-between gap-2">
                          <div>
                            <div className="font-mono font-semibold text-ink-primary">{att.file_name}</div>
                            <div className="text-[10px] font-mono text-ink-muted">Subido: {att.uploaded_at}</div>
                          </div>
                          <a
                            href={`/api/attachments/${att.id}/download`}
                            className="px-2.5 py-1 rounded border border-surface-border bg-surface-card hover:bg-surface-elevated font-mono text-[11px]"
                          >
                            Descargar
                          </a>
                        </div>
                      ))}
                    </div>

                    <div className="pt-3 border-t border-surface-border space-y-2">
                      <div className="font-serif font-bold text-ink-primary">Bitácora Cronológica Inmutable (A.3.14)</div>
                      {(selectedIncident.historial || []).map((h) => (
                        <div key={h.id} className="p-2.5 rounded bg-surface-ground border-l-2 border-[var(--unsa-primary)] text-[11px]">
                          <div className="flex justify-between font-mono text-ink-muted mb-0.5">
                            <span className="font-bold text-ink-primary">{h.event_type} • {h.actor}</span>
                            <span>{h.changed_at}</span>
                          </div>
                          <div className="text-ink-secondary">{h.description}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <window.StatusReasonModal
        modalState={statusModal}
        onClose={() => setStatusModal({ open: false, targetStatus: '', isReopen: false, incidentCode: '' })}
        onConfirm={(reason) => executeStatusChange(statusModal.targetStatus, reason)}
      />
    </div>
  );
};
