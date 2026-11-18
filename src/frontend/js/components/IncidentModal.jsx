// ==============================================================================
// Modales de Creación de Incidente (3 Pasos) y Justificación de Reapertura/Cierre
// ==============================================================================

window.IncidentCreateModal = function IncidentCreateModal({
  open,
  onClose,
  users,
  assets,
  controls,
  onCreated,
  showToast,
}) {
  const { useState, useEffect } = React;
  const today = new Date().toISOString().slice(0, 10);

  const initialForm = {
    title: '',
    description: '',
    incident_date: today,
    detection_date: today,
    asset_id: '',
    compromised_system: '',
    affected_url: '',
    involves_personal_data: true,
    incident_type: 'BF',
    severity: 'A',
    impact: 'A',
    iso27701_control_id: 'A.3.12',
    num_affected_subjects: 0,
    consequences_summary: '',
    assigned_to_id: '',
    initial_action_type: 'C',
    initial_action_description: '',
    create_mc_draft: true,
  };

  const [step, setStep] = useState(1);
  const [form, setForm] = useState(initialForm);
  const [ctrlSearch, setCtrlSearch] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setStep(1);
      setForm(initialForm);
      setCtrlSearch('');
    }
  }, [open]);

  if (!open) return null;

  const filteredControls = (controls || []).filter((c) => {
    if (!ctrlSearch.trim()) return true;
    const q = ctrlSearch.toLowerCase();
    return c.id.toLowerCase().includes(q) || (c.title || '').toLowerCase().includes(q);
  });

  const handleTogglePii = (val) => {
    setForm((prev) => ({
      ...prev,
      involves_personal_data: val,
      incident_type: val ? (prev.incident_type === 'IT' ? 'BF' : prev.incident_type) : 'IT',
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) {
      showToast('El título del incidente es obligatorio.', 'error');
      setStep(1);
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        asset_id: form.asset_id ? parseInt(form.asset_id, 10) : null,
        assigned_to_id: form.assigned_to_id ? parseInt(form.assigned_to_id, 10) : null,
        num_affected_subjects: parseInt(form.num_affected_subjects || 0, 10),
      };
      const res = await window.PIMS_API.apiFetch('/api/incidents', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        showToast(data.mensaje || 'Incidente registrado correctamente.', 'success');
        onCreated && onCreated(data.incident);
        onClose();
      } else {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || 'Error al registrar incidente.', 'error');
      }
    } catch (err) {
      showToast('Error de red al crear incidente.', 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-xs" style={{ backgroundColor: 'var(--modal-overlay)' }}>
      <div className="bg-surface-card border border-surface-border rounded max-w-2xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
          <div>
            <h3 className="font-serif font-bold text-sm text-ink-primary">
              Registrar Incidente / Brecha ISO/IEC 27701:2025
            </h3>
            <div className="text-[11px] font-mono text-ink-muted">
              Paso {step} de 3 • {step === 1 ? 'Identificación y Activo' : step === 2 ? 'Triaje B.3.12 y Control' : 'Responsable y Acción 10.2'}
            </div>
          </div>
          <button onClick={onClose} className="text-ink-muted hover:text-ink-primary text-sm px-2">✕</button>
        </div>

        {/* Step indicator */}
        <div className="grid grid-cols-3 border-b border-surface-border bg-surface-ground text-[11px] font-mono">
          {[1, 2, 3].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStep(s)}
              className={`py-2 px-3 text-left border-b-2 transition-colors ${
                step === s ? 'border-[var(--unsa-primary)] text-ink-primary font-bold bg-surface-card' : 'border-transparent text-ink-muted'
              }`}
            >
              {s}. {s === 1 ? 'Datos Básicos' : s === 2 ? 'Triaje B.3.12' : 'Asignación y MC'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {step === 1 && (
            <>
              <div>
                <label className="block font-semibold text-ink-primary mb-1">Título del Incidente *</label>
                <input
                  type="text"
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Ej. Exposición temporal de actas académicas en portal docente"
                  className="w-full px-3 py-2 rounded border border-surface-border bg-surface-ground text-ink-primary"
                />
              </div>
              <div>
                <label className="block font-semibold text-ink-primary mb-1">Descripción técnica de los hechos</label>
                <textarea
                  rows={3}
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Detalle el vector de detección, alcance preliminar y circunstancias..."
                  className="w-full px-3 py-2 rounded border border-surface-border bg-surface-ground text-ink-primary"
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-ink-primary mb-1">Fecha del Incidente</label>
                  <input
                    type="date"
                    value={form.incident_date}
                    onChange={(e) => setForm({ ...form, incident_date: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-ink-primary mb-1">Fecha de Detección</label>
                  <input
                    type="date"
                    value={form.detection_date}
                    onChange={(e) => setForm({ ...form, detection_date: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-ink-primary mb-1">Activo UNSA Afectado</label>
                  <select
                    value={form.asset_id}
                    onChange={(e) => setForm({ ...form, asset_id: e.target.value })}
                    className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                  >
                    <option value="">-- Seleccionar activo (opcional) --</option>
                    {(assets || []).map((a) => (
                      <option key={a.id} value={a.id}>[{a.code}] {a.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-ink-primary mb-1">Sistema / Endpoint / URL</label>
                  <input
                    type="text"
                    value={form.affected_url}
                    onChange={(e) => setForm({ ...form, affected_url: e.target.value })}
                    placeholder="https://..."
                    className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                  />
                </div>
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <div className="p-3 rounded bg-surface-ground border border-surface-border flex items-center justify-between">
                <div>
                  <div className="font-semibold text-ink-primary">¿Involucra Datos Personales (PII)? (ISO 27701 B.3.12 Note 1)</div>
                  <div className="text-[11px] text-ink-muted">Separa brechas de privacidad de incidentes técnicos operativos puros.</div>
                </div>
                <label className="inline-flex items-center gap-2 cursor-pointer font-mono font-bold">
                  <input
                    type="checkbox"
                    checked={form.involves_personal_data}
                    onChange={(e) => handleTogglePii(e.target.checked)}
                    className="w-4 h-4 accent-[var(--unsa-primary)]"
                  />
                  <span>{form.involves_personal_data ? 'SÍ (PII)' : 'NO (Técnico)'}</span>
                </label>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-ink-primary mb-1">Clasificación</label>
                  <select
                    value={form.incident_type}
                    onChange={(e) => setForm({ ...form, incident_type: e.target.value })}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                  >
                    <option value="BF">Brecha Confidencialidad (BF)</option>
                    <option value="BI">Brecha Integridad (BI)</option>
                    <option value="BD">Brecha Disponibilidad (BD)</option>
                    <option value="PI">No Conformidad Principios (PI)</option>
                    <option value="IT">Incidente Técnico sin PII (IT)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-ink-primary mb-1">Severidad</label>
                  <select
                    value={form.severity}
                    onChange={(e) => setForm({ ...form, severity: e.target.value, impact: e.target.value })}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                  >
                    <option value="C">Crítico (C)</option>
                    <option value="A">Alto (A)</option>
                    <option value="M">Medio (M)</option>
                    <option value="B">Bajo (B)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-ink-primary mb-1">Titulares Afectados</label>
                  <input
                    type="number"
                    min="0"
                    value={form.num_affected_subjects}
                    onChange={(e) => setForm({ ...form, num_affected_subjects: e.target.value })}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-ink-primary mb-1">Control ISO/IEC 27701:2025 Asociado</label>
                <input
                  type="text"
                  value={ctrlSearch}
                  onChange={(e) => setCtrlSearch(e.target.value)}
                  placeholder="Filtrar por código (ej. A.3.26) o nombre..."
                  className="w-full px-2.5 py-1.5 mb-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary text-[11px]"
                />
                <select
                  value={form.iso27701_control_id}
                  onChange={(e) => setForm({ ...form, iso27701_control_id: e.target.value })}
                  className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary font-mono"
                >
                  {filteredControls.map((c) => (
                    <option key={c.id} value={c.id}>{c.id} — {c.title}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-ink-primary mb-1">Consecuencias Observadas (B.3.12)</label>
                <textarea
                  rows={2}
                  value={form.consequences_summary}
                  onChange={(e) => setForm({ ...form, consequences_summary: e.target.value })}
                  placeholder="Impacto sobre titulares y operaciones..."
                  className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                />
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <div>
                <label className="block font-semibold text-ink-primary mb-1">Responsable Asignado (Empleado UNSA)</label>
                <select
                  value={form.assigned_to_id}
                  onChange={(e) => setForm({ ...form, assigned_to_id: e.target.value })}
                  className="w-full px-3 py-2 rounded border border-surface-border bg-surface-ground text-ink-primary"
                >
                  <option value="">-- Asignar por defecto al DPO --</option>
                  {(users || []).map((u) => (
                    <option key={u.id} value={u.id}>{u.full_name} — {u.position || u.area}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-ink-primary mb-1">Tipo Acción Inicial</label>
                  <select
                    value={form.initial_action_type}
                    onChange={(e) => setForm({ ...form, initial_action_type: e.target.value })}
                    className="w-full px-2.5 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                  >
                    <option value="C">Contención (C)</option>
                    <option value="R">Remediación (R)</option>
                    <option value="M">Mitigación (M)</option>
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className="block font-semibold text-ink-primary mb-1">Acción Inicial de Respuesta A.3.12 (opcional)</label>
                  <input
                    type="text"
                    value={form.initial_action_description}
                    onChange={(e) => setForm({ ...form, initial_action_description: e.target.value })}
                    placeholder="Ej. Bloqueo preventivo de endpoint afectado y rotación de credenciales"
                    className="w-full px-3 py-1.5 rounded border border-surface-border bg-surface-ground text-ink-primary"
                  />
                </div>
              </div>

              <label className="p-3 rounded bg-surface-ground border border-surface-border flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.create_mc_draft}
                  onChange={(e) => setForm({ ...form, create_mc_draft: e.target.checked })}
                  className="w-4 h-4 accent-[var(--unsa-primary)]"
                />
                <span>Generar automáticamente borrador de Formulario D34 de Medida Correctiva (Cláusula 10.2)</span>
              </label>
            </>
          )}

          {/* Footer Buttons */}
          <div className="pt-3 border-t border-surface-border flex items-center justify-between">
            <div>
              {step > 1 && (
                <button
                  type="button"
                  onClick={() => setStep(step - 1)}
                  className="px-3.5 py-1.5 rounded border border-surface-border bg-surface-card text-ink-primary hover:bg-surface-elevated"
                >
                  ← Anterior
                </button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3.5 py-1.5 rounded border border-surface-border bg-surface-card text-ink-secondary"
              >
                Cancelar
              </button>
              {step < 3 ? (
                <button
                  type="button"
                  onClick={() => setStep(step + 1)}
                  className="px-4 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white font-semibold"
                >
                  Siguiente →
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white font-semibold disabled:opacity-50"
                >
                  {saving ? 'Guardando...' : 'Registrar Incidente'}
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

window.StatusReasonModal = function StatusReasonModal({ modalState, onClose, onConfirm }) {
  const { useState, useEffect } = React;
  const [reason, setReason] = useState('');

  useEffect(() => {
    setReason('');
  }, [modalState?.open, modalState?.targetStatus]);

  if (!modalState?.open) return null;

  const isReopen = modalState.isReopen;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-xs" style={{ backgroundColor: 'var(--modal-overlay)' }}>
      <div className="bg-surface-card border border-surface-border rounded max-w-md w-full p-5 space-y-4 shadow-2xl">
        <div className="font-serif font-bold text-sm text-ink-primary">
          {isReopen ? 'Reabrir Expediente Cerrado' : 'Confirmar Cambio de Estado'}
        </div>
        <p className="text-xs text-ink-secondary leading-relaxed">
          {isReopen
            ? `Está por reabrir el incidente ${modalState.incidentCode} hacia estado ${modalState.targetStatus}. Registre la justificación obligatoria para la bitácora A.3.14:`
            : `¿Confirma cambiar el estado de ${modalState.incidentCode} a '${modalState.targetStatus}'?`}
        </p>
        <textarea
          rows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder={isReopen ? 'Motivo obligatorio de reapertura...' : 'Observación opcional para bitácora...'}
          className="w-full px-3 py-2 rounded border border-surface-border bg-surface-ground text-xs text-ink-primary"
        />
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded border border-surface-border text-xs text-ink-secondary"
          >
            Cancelar
          </button>
          <button
            type="button"
            disabled={isReopen && !reason.trim()}
            onClick={() => onConfirm(reason)}
            className="px-4 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold disabled:opacity-50"
          >
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
};
