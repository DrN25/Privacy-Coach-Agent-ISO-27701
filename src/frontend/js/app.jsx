// Setup marked options for clean GitHub-Flavored Markdown
if (window.marked) {
  window.marked.setOptions({
    gfm: true,
    breaks: true
  });
}

const { useState, useEffect, useMemo, useRef } = React;

function App() {
  const [status, setStatus] = useState(null);
  const [archivos, setArchivos] = useState([]);
  const [inventario, setInventario] = useState([]);
  const [clausulas, setClausulas] = useState([]);
  const [hallazgos, setHallazgos] = useState([]);
  const [resumen, setResumen] = useState({});
  const [mockupsDisponibles, setMockupsDisponibles] = useState([]);
  
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'documents', 'database'
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [subgraphData, setSubgraphData] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [reanalysisNeeded, setReanalysisNeeded] = useState(false);
  const [toast, setToast] = useState(null);
  
  // Custom React Confirmation Modal (replaces window.confirm)
  const [confirmModal, setConfirmModal] = useState({ open: false, title: '', message: '', onConfirm: null });
  
  // Modal de referencia legal (controles ISO, artículos Ley, sanciones ANPD)
  const [legalRefModal, setLegalRefModal] = useState({ open: false, tipo: '', data: null, loading: false });

  const handleExportDictamen = (finding) => {
    if (!finding) return;
    const fid = finding.codigo_regla || finding.id;
    window.open(`/api/export-dictamen/${encodeURIComponent(fid)}`, '_blank');
  };

  const formatMarkdownCitations = (content) => {
    if (!content) return '';
    let parsed = window.marked ? window.marked.parse(content) : content;
    // Replace ISO controls: A.1.4.5, A.3.24
    parsed = parsed.replace(/\b(A\.\d+\.\d+(?:\.\d+)?)\b/g, (match) => {
      return `<button type="button" class="inline-flex items-center px-1.5 py-0.5 mx-0.5 text-[10px] font-mono font-medium rounded bg-cyan-950 text-cyan-300 border border-cyan-800 hover:bg-cyan-900 transition-colors cursor-pointer" onclick="window.fetchLegalRefGlobal && window.fetchLegalRefGlobal('control','${match}')">${match} [Ref]</button>`;
    });
    // Replace Ley articles: Art. 13, Art 13, Artículo 13
    parsed = parsed.replace(/\b(?:Art(?:ículo|\.)?\s*)(\d+)\b/g, (match, num) => {
      return `<button type="button" class="inline-flex items-center px-1.5 py-0.5 mx-0.5 text-[10px] font-mono font-medium rounded bg-violet-950 text-violet-300 border border-violet-800 hover:bg-violet-900 transition-colors cursor-pointer" onclick="window.fetchLegalRefGlobal && window.fetchLegalRefGlobal('articulo','Art_${num}')">Art. ${num} [Ley]</button>`;
    });
    return parsed;
  };

  
  // Panel de precedentes expandido
  const [precedentPanel, setPrecedentPanel] = useState({ open: false, findingId: null });
  
  // Filtros de búsqueda en BD
  const [searchColumna, setSearchColumna] = useState('');
  const [filterCategoria, setFilterCategoria] = useState('ALL');

  const chatBottomRef = useRef(null);

  useEffect(() => {
    fetchStatus();
    fetchMockups();
    loadDatabase();
  }, []);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, loading]);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3800);
  };

  // Fetch legal reference from backend
  const fetchLegalRef = async (tipo, refId) => {
  window.fetchLegalRefGlobal = fetchLegalRef;

    setLegalRefModal({ open: true, tipo, data: null, loading: true });
    try {
      const res = await fetch('/api/legal-reference/' + encodeURIComponent(tipo) + '/' + encodeURIComponent(refId));
      if (!res.ok) throw new Error('Referencia no encontrada');
      const data = await res.json();
      setLegalRefModal({ open: true, tipo, data, loading: false });
    } catch (e) {
      setLegalRefModal({ open: true, tipo, data: { error: e.message }, loading: false });
    }
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      setStatus(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchMockups = async () => {
    try {
      const res = await fetch('/api/mockups');
      const data = await res.json();
      setMockupsDisponibles(data.mockups || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadDatabase = async () => {
    try {
      const res = await fetch('/api/database-view');
      const data = await res.json();
      setArchivos(data.archivos || []);
      setInventario(data.inventario || []);
      setClausulas(data.clausulas || []);
      setHallazgos(data.hallazgos || []);
      setResumen(data.resumen_impacto || {});

      if (data.hallazgos && data.hallazgos.length > 0 && !selectedFinding) {
        handleSelectFinding(data.hallazgos[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // 1. REINICIAR DESDE CERO (Nueva Empresa)
  const requestReset = () => {
    setConfirmModal({
      open: true,
      title: "Comenzar Auditoría desde Cero",
      message: "¿Deseas borrar los documentos e inventario de la empresa? Tu espacio quedará limpio para una prueba desde cero.",
      confirmText: "Reiniciar Todo",
      confirmColor: "bg-rose-600 hover:bg-rose-500",
      onConfirm: async () => {
        setLoading(true);
        setLoadingMsg("Limpiando base de datos y memoria SQLite...");
        try {
          const res = await fetch('/api/reset', { method: 'POST' });
          const data = await res.json();
          setSelectedFinding(null);
          setSubgraphData(null);
          setChatHistory([]);
          setReanalysisNeeded(false);
          await loadDatabase();
          await fetchStatus();
          showToast(data.mensaje, "success");
        } catch (e) {
          showToast("Error al reiniciar: " + e.message, "error");
        } finally {
          setLoading(false);
          setConfirmModal({ open: false });
        }
      }
    });
  };

  // 2. CARGAR CASO COMPLETO SALUDTOTAL
  const handleLoadFullCase = async () => {
    setLoading(true);
    setLoadingMsg("Cargando caso completo: DDL SQL, Políticas PDF, SLA Cloud y Diccionario...");
    try {
      const res = await fetch('/api/load-mockups', { method: 'POST' });
      const data = await res.json();
      setReanalysisNeeded(false);
      await loadDatabase();
      await fetchStatus();
      showToast(data.mensaje, "success");
    } catch (e) {
      showToast("Error: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  // 3. CARGAR UN MOCKUP INDIVIDUAL
  const handleLoadSingleMockup = async (filename) => {
    setLoading(true);
    setLoadingMsg(`Cargando e incorporando ${filename} a la BD...`);
    try {
      const res = await fetch(`/api/load-single-mockup/${filename}`, { method: 'POST' });
      const data = await res.json();
      setReanalysisNeeded(true);
      await loadDatabase();
      await fetchStatus();
      showToast(data.mensaje, "success");
    } catch (e) {
      showToast("Error: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  // 4. SUBIR ARCHIVO MANUAL
  const handleUploadFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setLoadingMsg(`Parseando ${file.name} con AST sqlglot / PyMuPDF...`);
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setReanalysisNeeded(true);
      await loadDatabase();
      await fetchStatus();
      showToast(data.mensaje, "success");
    } catch (e) {
      showToast("Error: " + e.message, "error");
    } finally {
      setLoading(false);
      e.target.value = '';
    }
  };

  // 5. ELIMINAR DOCUMENTO (Con modal propio de React)
  const requestDeleteDocument = (id, nombre) => {
    setConfirmModal({
      open: true,
      title: "Eliminar Documento del Repositorio",
      message: `¿Seguro que deseas eliminar '${nombre}'? Se removerán sus columnas asociadas de SQLite y se requerirá un reanálisis.`,
      confirmText: "Eliminar",
      confirmColor: "bg-rose-600 hover:bg-rose-500",
      onConfirm: async () => {
        setLoading(true);
        setLoadingMsg(`Removiendo ${nombre} de la base de datos...`);
        try {
          const res = await fetch(`/api/documents/${id}`, { method: 'DELETE' });
          const data = await res.json();
          setReanalysisNeeded(true);
          await loadDatabase();
          await fetchStatus();
          showToast(data.mensaje, "success");
        } catch (e) {
          showToast("Error al eliminar: " + e.message, "error");
        } finally {
          setLoading(false);
          setConfirmModal({ open: false });
        }
      }
    });
  };

  // 6. EJECUTAR REANÁLISIS
  const handleReanalyze = async () => {
    setLoading(true);
    setLoadingMsg("Ejecutando Reanálisis de Privacidad (DSPM + Router O(1))...");
    try {
      const res = await fetch('/api/reanalyze', { method: 'POST' });
      const data = await res.json();
      setReanalysisNeeded(false);
      await loadDatabase();
      showToast(data.mensaje, "success");
    } catch (e) {
      showToast("Error en reanálisis: " + e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  // 7. SELECCIONAR HALLAZGO Y EXTRAER SUBGRAFO
  const handleSelectFinding = async (finding) => {
    setSelectedFinding(finding);
    try {
      const res = await fetch(`/api/subgraph/${finding.control_iso27701}`);
      const data = await res.json();
      setSubgraphData(data);
    } catch (e) {
      console.error(e);
    }

    setChatHistory([
      {
        role: "assistant",
        content: `### Expediente de Auditoría: No Conformidad ${finding.codigo_regla}

* **Activo / Elemento:** \`${finding.elemento_afectado}\`
* **Control ISO/IEC 27701:2025:** \`${finding.control_iso27701}\` (${finding.control_nombre || 'Seguridad en Tratamiento'})
* **Tipificación Ley 29733:** ${finding.articulo_ley29733}
* **Exposición Sancionadora ANPD:** **${finding.multa_estimada_uit} UIT** (S/ ${finding.multa_estimada_pen.toLocaleString('es-PE')})
* **Precedente:** ${finding.precedente_anpd || 'Resolución Directoral ANPD'}

Selecciona una acción técnica rápida o ingresa un requerimiento pericial.`
      }
    ]);
  };

  // 8. ENVIAR MENSAJE AL COACH (OpenRouter DeepSeek v4.1 Flash)
  const handleSendMessage = async (promptOverride = null, findingOverride = null) => {
    const currentFinding = findingOverride || selectedFinding;
    const textToSend = promptOverride || chatInput.trim();
    if (!textToSend || !currentFinding) return;

    if (findingOverride && (!selectedFinding || selectedFinding.id !== findingOverride.id)) {
      setSelectedFinding(findingOverride);
    }

    const newHistory = [...chatHistory, { role: "user", content: textToSend }];
    setChatHistory(newHistory);
    if (!promptOverride) setChatInput('');

    setChatLoading(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hallazgo_id: currentFinding.id,
          mensaje_usuario: textToSend,
          historial: newHistory.slice(-6)
        })
      });
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Servidor devolvió código ${res.status}: ${errorText.slice(0, 100)}`);
      }
      const data = await res.json();
      setChatHistory(prev => [
        ...prev,
        {
          role: "assistant",
          content: data.mensaje || data.error || "Dictamen generado.",
          reasoning: data.reasoning,
          sql_patch: data.sql_patch
        }
      ]);
    } catch (e) {
      setChatHistory(prev => [
        ...prev,
        { role: "assistant", content: "Error al consultar al Auditor de Cumplimiento: " + e.message }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // 9. MARCAR COMO REMEDIADO
  const handleRemediate = async () => {
    if (!selectedFinding) return;
    try {
      const res = await fetch('/api/remediate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hallazgo_id: selectedFinding.id,
          parche_sql: "-- Remediado"
        })
      });
      const data = await res.json();
      showToast(data.mensaje, "success");
      await loadDatabase();
    } catch (e) {
      showToast("Error: " + e.message, "error");
    }
  };

  // Filtros de inventario
  const inventarioFiltrado = useMemo(() => {
    return inventario.filter(item => {
      const matchesSearch = item.nombre_columna.toLowerCase().includes(searchColumna.toLowerCase()) ||
                            item.nombre_tabla.toLowerCase().includes(searchColumna.toLowerCase());
      const matchesCat = filterCategoria === 'ALL' || item.categoria_sensible === filterCategoria;
      return matchesSearch && matchesCat;
    });
  }, [inventario, searchColumna, filterCategoria]);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#070a12] text-slate-100 font-sans">
      
      {/* NAVBAR DE INGENIERÍA */}
      <header className="glass-header sticky top-0 z-40 px-6 py-3 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-tight text-white">Privacy & DSPM Multi-Agent System</h1>
              <span className="text-[10px] bg-cyan-950/90 text-cyan-300 font-mono px-2 py-0.5 rounded-full border border-cyan-800/60 font-semibold">
                ISO 27701:2025 • Ley 29733
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Trabajo de Investigación Formativa — Auditoría de Sistemas (UNSA)</p>
          </div>
        </div>

        {/* Action Center in Header */}
        <div className="flex items-center gap-3">
          <button
            onClick={requestReset}
            className="px-3 py-1.5 rounded-lg bg-slate-900/90 hover:bg-rose-950/60 hover:text-rose-300 hover:border-rose-800/80 border border-slate-800 text-xs font-semibold text-slate-300 transition-all flex items-center gap-1.5"
            title="Borra la base de datos de la empresa para empezar una prueba limpia"
          >
            <svg className="w-3.5 h-3.5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            <span>Nueva Empresa (Reset 0)</span>
          </button>

          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-400">LLM:</span>
            <span className="text-cyan-300 font-bold">{status?.llm_model || 'deepseek/deepseek-v4.1-flash'}</span>
          </div>
        </div>
      </header>

      {/* BARRA DE PROGRESO DE REMEDIACIÓN */}
      {hallazgos.length > 0 && (
        <div className="mx-6 mt-3 flex items-center gap-3">
          <div className="flex-1 h-2 rounded-full bg-slate-800 overflow-hidden">
            <div 
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-700"
              style={{ width: `${hallazgos.length > 0 ? (hallazgos.filter(h => h.estado === 'REMEDIADO').length / hallazgos.length * 100) : 0}%` }}
            />
          </div>
          <span className="text-[11px] font-mono text-slate-400 whitespace-nowrap">
            {hallazgos.filter(h => h.estado === 'REMEDIADO').length}/{hallazgos.length} remediados
          </span>
          {hallazgos.filter(h => h.estado === 'REMEDIADO').length === hallazgos.length && hallazgos.length > 0 && (
            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-700">✓ Completo</span>
          )}
        </div>
      )}

      {/* POPUP / MODAL DE REANÁLISIS OBLIGATORIO (TRIGGER REACTIVO) */}
      {reanalysisNeeded && (
        <div className="mx-6 mt-3 p-3 rounded-xl bg-gradient-to-r from-amber-950/90 to-slate-900 border border-amber-500/70 shadow-2xl flex items-center justify-between gap-4 animate-pulse-slow">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
            </div>
            <div>
              <h4 className="text-xs font-bold text-amber-200">Repositorio Documental Modificado</h4>
              <p className="text-[11px] text-amber-300/80">Se añadieron o eliminaron documentos de la empresa. Se requiere un reanálisis para sincronizar las brechas y multas.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleReanalyze}
              className="py-1.5 px-4 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs shadow-md shadow-amber-500/20 transition-all flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
              <span>Ejecutar reanálisis</span>
            </button>
            <button
              onClick={() => setReanalysisNeeded(false)}
              className="py-1.5 px-3 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-200 text-xs"
            >
              Descartar
            </button>
          </div>
        </div>
      )}

      {/* BANNER DEL EMBUDO QUIRÚRGICO */}
      <div className="mx-6 mt-3 p-3 rounded-xl glass-card flex flex-col md:flex-row items-center justify-between gap-3 text-xs border border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-violet-400 font-bold flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/></svg>
            Embudo de Reducción:
          </span>
          <span className="text-slate-400 text-[11px]">De 150,000 tokens normativos a 850 tokens quirúrgicos para el Auditor</span>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[10px]">
          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">150k Normas</span>
          <span className="text-slate-600">→</span>
          <span className="px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800 text-cyan-300">AST & 3 Candados</span>
          <span className="text-slate-600">→</span>
          <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300">Router O(1) 0.2ms</span>
          <span className="text-slate-600">→</span>
          <span className="px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800 text-rose-300 font-bold">850t Payload Auditor</span>
        </div>
      </div>

      {/* METRICAS DE IMPACTO FINANCIERO */}
      <div className="mx-6 mt-3 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="glass-card p-3 border-slate-800">
          <span className="text-[11px] text-slate-400">Documentos Activos</span>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-xl font-bold font-mono text-white">{archivos.length}</span>
            <span className="text-[10px] text-slate-500 font-mono">{inventario.length} columnas en BD</span>
          </div>
        </div>
        <div className="glass-card p-3 border-slate-800">
          <span className="text-[11px] text-slate-400">Brechas Detectadas</span>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-xl font-bold font-mono text-rose-400">{resumen.total_brechas || 0}</span>
            <span className="text-[10px] text-rose-400/80 font-bold font-mono">{resumen.brechas_criticas || 0} críticas</span>
          </div>
        </div>
        <div className="glass-card p-3 border-slate-800">
          <span className="text-[11px] text-slate-400">Multa Total ANPD</span>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-xl font-bold font-mono text-amber-400">{resumen.multa_total_uit || 0} UIT</span>
            <span className="text-[10px] text-slate-400 font-mono">Ley N.° 29733</span>
          </div>
        </div>
        <div className="glass-card p-3 border-slate-800">
          <span className="text-[11px] text-slate-400">Exposición en Soles</span>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-lg font-bold font-mono text-emerald-400">
              S/ {(resumen.multa_total_pen || 0).toLocaleString('es-PE', { minimumFractionDigits: 2 })}
            </span>
            <span className="text-[10px] text-slate-500">Estimación ANPD</span>
          </div>
        </div>
      </div>

      {/* ESTADO VACÍO: PROBAR DESDE CERO */}
      {archivos.length === 0 ? (
        <div className="mx-6 my-8 p-12 glass-card border-dashed border-2 border-slate-800 rounded-2xl flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-600/20 to-violet-600/20 border border-cyan-500/30 flex items-center justify-center mb-4 shadow-lg shadow-cyan-500/10">
            <svg className="w-8 h-8 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
          </div>
          <h2 className="text-lg font-bold text-white mb-2">Comienza la Auditoría de tu Empresa desde Cero</h2>
          <p className="text-xs text-slate-400 max-w-lg mb-6 leading-relaxed">
            Actualmente no hay ningún documento cargado en la base de datos interna SQLite (KB-3). Sube los archivos reales de tu empresa o carga el pack de prueba de la clínica "SaludTotal S.A.C." para comprobar el funcionamiento.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4">
            <button
              onClick={handleLoadFullCase}
              className="py-3 px-6 rounded-xl bg-gradient-to-r from-cyan-600 to-violet-600 hover:from-cyan-500 hover:to-violet-500 font-bold text-xs text-white shadow-lg shadow-cyan-600/20 transition-all flex items-center gap-2"
            >
              <svg className="w-4 h-4 text-cyan-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              <span>Cargar caso SaludTotal (4 archivos)</span>
            </button>

            <label className="py-3 px-6 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700 text-xs font-semibold text-slate-200 cursor-pointer transition-all flex items-center gap-2">
              <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
              <span>Subir Archivo Propio (SQL, PDF, MD, TXT)</span>
              <input type="file" className="hidden" onChange={handleUploadFile} accept=".sql,.pdf,.md,.txt" />
            </label>
          </div>

          {/* Carga Selectiva de Archivos Individuales */}
          <div className="mt-8 pt-6 border-t border-slate-800/80 w-full max-w-2xl text-left">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-3 text-center">O añade archivos individuales para probar la ingesta progresiva:</span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {mockupsDisponibles.map(m => (
                <button
                  key={m.nombre}
                  onClick={() => handleLoadSingleMockup(m.nombre)}
                  className="p-3 rounded-xl bg-slate-900/90 hover:bg-slate-800/90 border border-slate-800 hover:border-slate-700 text-left text-xs transition-all flex items-center justify-between"
                >
                  <div>
                    <span className="text-[10px] font-mono text-cyan-400 font-bold block">{m.tipo}</span>
                    <span className="text-slate-200 font-medium truncate block max-w-xs">{m.nombre}</span>
                    <span className="text-[10px] text-slate-500 block">{m.descripcion}</span>
                  </div>
                  <span className="text-xs text-cyan-400 font-bold px-2 py-1 bg-cyan-950/60 rounded border border-cyan-800">+ Cargar</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* WORKSPACE COMPLETO CUANDO HAY DOCUMENTOS */
        <main className="flex-1 px-6 py-4 grid grid-cols-1 lg:grid-cols-12 gap-4">
          
          {/* COLUMNA IZQUIERDA (7 cols): DOCUMENTOS + BD SQLITE + BRECHAS */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            
            {/* GESTOR DOCUMENTAL CON AGREGAR Y ELIMINAR */}
            <div className="glass-card p-4 border-slate-800">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Documentos en Repositorio de la Empresa ({archivos.length})
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <label className="py-1 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 cursor-pointer transition-all flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                    <span>Agregar Archivo</span>
                    <input type="file" className="hidden" onChange={handleUploadFile} accept=".sql,.pdf,.md,.txt" />
                  </label>
                </div>
              </div>

              {/* Grid de documentos */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-3 max-h-48 overflow-y-auto pr-1">
                {archivos.map(doc => (
                  <div key={doc.id} className="p-3 rounded-xl bg-slate-900/90 border border-slate-800/80 flex items-center justify-between gap-2 hover:border-slate-700 transition-all">
                    <div className="flex items-center gap-2.5 overflow-hidden">
                      <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-mono text-[10px] font-bold text-cyan-300 shrink-0">
                        {doc.tipo_archivo}
                      </div>
                      <div className="overflow-hidden">
                        <span className="text-xs font-semibold text-slate-200 block truncate" title={doc.nombre_archivo}>{doc.nombre_archivo}</span>
                        <span className="text-[10px] text-slate-500 font-mono">{(doc.tamano_bytes / 1024).toFixed(1)} KB • {doc.fecha_carga.split(' ')[0]}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => requestDeleteDocument(doc.id, doc.nombre_archivo)}
                      className="text-slate-500 hover:text-rose-400 p-1.5 rounded hover:bg-slate-800 transition-colors"
                      title="Eliminar documento del repositorio"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* BASE DE DATOS DE LA EMPRESA (INVENTARIO Y CLÁUSULAS SQLITE) */}
            <div className="glass-card p-4 border-slate-800 flex flex-col h-72">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setActiveTab('overview')}
                    className={`text-xs font-bold uppercase tracking-wider pb-1 transition-colors ${activeTab === 'overview' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-slate-400 hover:text-slate-200'}`}
                  >
                    Inventario de Columnas ({inventario.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('clauses')}
                    className={`text-xs font-bold uppercase tracking-wider pb-1 transition-colors ${activeTab === 'clauses' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-slate-400 hover:text-slate-200'}`}
                  >
                    Cláusulas Legales ({clausulas.length})
                  </button>
                </div>

                {/* Filtro rápido */}
                {activeTab === 'overview' && (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      placeholder="Buscar columna o tabla..."
                      value={searchColumna}
                      onChange={(e) => setSearchColumna(e.target.value)}
                      className="bg-slate-900 border border-slate-700/80 rounded-lg px-2.5 py-1 text-[11px] text-white focus:outline-none focus:border-cyan-500 w-36"
                    />
                    <select
                      value={filterCategoria}
                      onChange={(e) => setFilterCategoria(e.target.value)}
                      className="bg-slate-900 border border-slate-700/80 rounded-lg px-2 py-1 text-[11px] text-slate-300 focus:outline-none"
                    >
                      <option value="ALL">Todas</option>
                      <option value="DATOS_SALUD">Salud</option>
                      <option value="CREDENCIALES_ACCESO">Credenciales</option>
                      <option value="DATOS_ECONOMICOS">Económicos</option>
                      <option value="DATOS_IDENTIFICACION">Identificación</option>
                    </select>
                  </div>
                )}
              </div>

              {activeTab === 'clauses' ? (
                <div className="flex-1 overflow-y-auto mt-2">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead className="sticky top-0 bg-slate-900 text-[10px] text-slate-400 uppercase">
                      <tr>
                        <th className="p-2">Documento</th>
                        <th className="p-2">Cláusula</th>
                        <th className="p-2">Tipo</th>
                        <th className="p-2">Texto Extraído</th>
                      </tr>
                    </thead>
                    <tbody>
                      {clausulas.map(c => (
                        <tr key={c.id} className="border-b border-slate-800/60 hover:bg-slate-800/30">
                          <td className="p-2 font-mono text-violet-400 text-[11px]">{c.documento}</td>
                          <td className="p-2 font-semibold text-slate-200">{c.numero_clausula}: {c.titulo_clausula}</td>
                          <td className="p-2"><span className="px-1.5 py-0.5 rounded text-[9px] bg-amber-500/20 text-amber-300">{c.tipo_clausula}</span></td>
                          <td className="p-2 text-slate-400 truncate max-w-xs">{c.texto_clausula}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="flex-1 overflow-y-auto mt-2">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead className="sticky top-0 bg-slate-900 text-[10px] text-slate-400 uppercase">
                      <tr>
                        <th className="p-2">Tabla</th>
                        <th className="p-2">Columna</th>
                        <th className="p-2">Tipo SQL</th>
                        <th className="p-2">Categoría LPDP</th>
                        <th className="p-2">Confianza</th>
                        <th className="p-2">Recomendación</th>
                      </tr>
                    </thead>
                    <tbody>
                      {inventarioFiltrado.map(item => (
                        <tr key={item.id} className="border-b border-slate-800/60 hover:bg-slate-800/30">
                          <td className="p-2 font-mono text-cyan-400 font-semibold">{item.nombre_tabla}</td>
                          <td className="p-2 font-mono text-slate-200">{item.nombre_columna}</td>
                          <td className="p-2 font-mono text-slate-400">{item.tipo_sql}</td>
                          <td className="p-2">
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                              item.categoria_sensible === 'DATOS_SALUD' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                              item.categoria_sensible === 'DATOS_ECONOMICOS' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                              item.categoria_sensible === 'CREDENCIALES_ACCESO' ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30' :
                              'bg-slate-800 text-slate-300'
                            }`}>
                              {item.categoria_sensible}
                            </span>
                          </td>
                          <td className="p-2 text-emerald-400 font-mono">{(item.nivel_confianza * 100).toFixed(0)}%</td>
                          <td className="p-2 text-slate-400 truncate max-w-xs">{item.recomendacion_seguridad}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* LISTA DE BRECHAS CON BOTONES RÁPIDOS DE CONTEXTO */}
            <div className="glass-card p-4 border-slate-800 flex-1">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                  Brechas Identificadas ({hallazgos.length})
                </h3>
                <span className="text-[11px] text-slate-400">Pulsa los botones rápidos para consultar directamente al Auditor</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[380px] overflow-y-auto pr-1">
                {hallazgos.map(h => {
                  const isSelected = selectedFinding?.id === h.id;
                  const isRemediated = h.estado === 'REMEDIADO';
                  return (
                    <div
                      key={h.id}
                      onClick={() => handleSelectFinding(h)}
                      className={`p-3.5 rounded-xl glass-card cursor-pointer border transition-all ${
                        isSelected ? 'border-cyan-500 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/50' : 'border-slate-800 hover:border-slate-700'
                      } ${isRemediated ? 'opacity-60 border-emerald-700' : ''}`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-xs font-bold text-cyan-400 px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800">
                            {h.codigo_regla}
                          </span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelectFinding(h);
                              fetchLegalRef('control', h.control_iso27701);
                            }}
                            className="font-mono text-[10px] font-bold text-slate-300 hover:text-cyan-300 px-1.5 py-0.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-700 transition-colors"
                            title={`Abrir control oficial ${h.control_iso27701}`}
                          >
                            {h.control_iso27701}
                          </button>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                            h.nivel_riesgo === 'CRÍTICO' ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' :
                            h.nivel_riesgo === 'ALTO' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                            'bg-blue-500/20 text-blue-400 border-blue-500/30'
                          }`}>
                            {h.nivel_riesgo}
                          </span>
                        </div>
                        <div className="text-right font-mono">
                          <span className="text-xs font-bold text-rose-400">{h.multa_estimada_uit} UIT</span>
                          <span className="text-[9px] text-slate-500 block">S/ {h.multa_estimada_pen.toLocaleString('es-PE')}</span>
                        </div>
                      </div>

                      <h4 className="text-xs font-semibold text-slate-100 mb-1">{h.titulo}</h4>
                      <p className="text-[11px] text-slate-400 line-clamp-2 mb-2.5">{h.descripcion}</p>

                      {/* ACCIONES CONTEXTUALES DINÁMICAS */}
                      <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1">
                        {(() => {
                          const cat = (h.codigo_regla || '').toUpperCase();
                          const isTech = ['R-001','R-002','R-003','R-004','R-005'].some(r => cat.includes(r)) || 
                                         (h.origen_archivo || '').endsWith('.sql');
                          const isARCO = cat.includes('R-007') || (h.titulo || '').toLowerCase().includes('arco');
                          const isContract = cat.includes('R-006') || (h.titulo || '').toLowerCase().includes('contrato') || 
                                             (h.titulo || '').toLowerCase().includes('sla');
                          
                          const prompts = [];
                          
                          // Diagnóstico
                          prompts.push({
                            label: 'Diagnóstico',
                            color: 'hover:bg-cyan-950 text-cyan-300',
                            prompt: `¿Cuál es el diagnóstico pericial y fundamento jurídico de la vulnerabilidad en ${h.activo_afectado || 'el activo'} según el control ${h.control_iso27701} y la Ley 29733?`
                          });
                          
                          if (isTech) {
                            prompts.push({
                              label: 'Remediación SQL',
                              color: 'hover:bg-emerald-950 text-emerald-300',
                              prompt: `Genera el script SQL de remediación defensiva para la brecha ${h.codigo_regla}: ${h.titulo}. Incluye ALTER TABLE con pgcrypto si aplica cifrado, o DROP/PURGE si corresponde eliminar el dato.`
                            });
                          }
                          
                          if (isARCO) {
                            prompts.push({
                              label: 'Redacción Política',
                              color: 'hover:bg-emerald-950 text-emerald-300',
                              prompt: `Redacta la cláusula correctiva para la política de privacidad que resuelva la brecha ${h.codigo_regla}: ${h.titulo}. Incluye los canales ARCO que deben habilitarse y la verificación de identidad proporcional.`
                            });
                          }
                          
                          if (isContract) {
                            prompts.push({
                              label: 'Cláusula Contractual',
                              color: 'hover:bg-emerald-950 text-emerald-300',
                              prompt: `Redacta las cláusulas contractuales de blindaje legal para remediar la brecha ${h.codigo_regla}: ${h.titulo}. Incluye requisitos DPA, SLA de seguridad y obligaciones del encargado.`
                            });
                          }
                          
                          if (!isTech && !isARCO && !isContract) {
                            prompts.push({
                              label: 'Remediación',
                              color: 'hover:bg-emerald-950 text-emerald-300',
                              prompt: `Recomienda las acciones de remediación concretas (técnicas, legales y organizativas) para cerrar la brecha ${h.codigo_regla}: ${h.titulo}.`
                            });
                          }
                          
                          // Precedentes ANPD
                          prompts.push({
                            label: 'Precedentes ANPD',
                            color: 'hover:bg-violet-950 text-violet-300',
                            prompt: `¿Cuál es el precedente sancionador de la ANPD más análogo a este caso y cómo se cuantificó la multa de ${h.multa_estimada_uit || 0} UIT? Cita la resolución directoral específica.`
                          });
                          
                          return (
                            <>
                              {prompts.map((p, i) => (
                                <button
                                  key={i}
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleSelectFinding(h);
                                    handleSendMessage(p.prompt, h);
                                  }}
                                  className={`px-2 py-1 rounded bg-slate-800/90 ${p.color} border border-slate-700 text-[10px] font-semibold transition-colors`}
                                >
                                  {p.label}
                                </button>
                              ))}
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleSelectFinding(h);
                                  fetchLegalRef('control', h.control_iso27701);
                                }}
                                className="px-2 py-1 rounded bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 text-[10px] font-semibold transition-colors"
                                title={`Abrir ficha técnica y fundamentos del control ${h.control_iso27701}`}
                              >
                                Control {h.control_iso27701}
                              </button>
                            </>
                          );
                        })()}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>

          {/* COLUMNA DERECHA (5 cols): AUDITOR DE CUMPLIMIENTO & REMEDIACIÓN + SUBGRAFO */}
          <div className="lg:col-span-5 flex flex-col gap-4">
            
            {/* SUBGRAFO NORMATIVO */}
            {selectedFinding && (
              <div className="glass-card p-4 border-slate-800">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-cyan-400">{selectedFinding.codigo_regla}</span>
                    <h4 className="text-xs font-bold text-white truncate max-w-xs">{selectedFinding.titulo}</h4>
                  </div>
                  <span className="text-xs font-bold text-rose-400 font-mono">{selectedFinding.multa_estimada_uit} UIT</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 my-2">
                  <div>
                    <span className="text-slate-500 block">Elemento:</span>
                    <strong className="text-slate-200 font-mono truncate block">{selectedFinding.elemento_afectado}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Riesgo Económico:</span>
                    <strong className="text-amber-400 font-mono">S/ {selectedFinding.multa_estimada_pen.toLocaleString('es-PE')}</strong>
                  </div>
                </div>

                <h5 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                  <svg className="w-3 h-3 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                  <span>Subgrafo Normativo (ISO 27701 ↔ ISO 29100 ↔ Ley 29733)</span>
                </h5>
                <div className="max-h-28 overflow-y-auto space-y-1.5 pr-1">
                  {subgraphData?.subgrafo_nodos?.map(n => (
                    <div 
                      key={n.id} 
                      className="p-2 rounded bg-slate-900 border border-slate-800 text-[11px] cursor-pointer hover:border-cyan-600 hover:bg-slate-800/80 transition-all group"
                      onClick={() => {
                        if (n.tipo === 'ISO27701_CONTROL') fetchLegalRef('control', n.id);
                        else if (n.tipo === 'ANPD_SANCTION') fetchLegalRef('sancion', String(n.id).replace('ANPD-',''));
                        else if (n.tipo === 'ISO29100_PRINCIPLE') showToast('Principio ' + n.id + ': ' + n.label, 'info');
                      }}
                      title="Click para ver contenido original"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-cyan-400 font-bold group-hover:text-cyan-300">{n.id}</span>
                        <span className="text-[9px] bg-slate-800 text-slate-300 px-1 rounded">{n.tipo}</span>
                      </div>
                      <p className="text-slate-200 font-medium mt-0.5 group-hover:text-white">{n.label}</p>
                      {n.peru_bridge && (
                        <p className="text-slate-400 text-[10px] mt-1 border-t border-slate-800/80 pt-0.5">
                          <span className="text-emerald-400 font-medium">Perú:</span>{' '}
                          <span 
                            className="underline decoration-dotted cursor-pointer hover:text-emerald-300"
                            onClick={(e) => { 
                              e.stopPropagation(); 
                              const match = n.peru_bridge.ley_29733.match(/Art\.?\s*(\d+)/);
                              if (match) fetchLegalRef('articulo', 'Art_' + match[1]);
                            }}
                          >{n.peru_bridge.ley_29733}</span>
                        </p>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* PRECEDENTES ANPD DEL GRAFO (datos duros sin LLM) */}
                {subgraphData?.sanciones_anpd?.length > 0 && (
                  <div className="mt-3">
                    <h5 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                      <svg className="w-3 h-3 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"/></svg>
                      Precedentes ANPD Vinculados
                    </h5>
                    <div className="space-y-1.5">
                      {subgraphData.sanciones_anpd.map((s, i) => (
                        <div 
                          key={i} 
                          className="p-2 rounded bg-violet-950/30 border border-violet-800/40 text-[11px] cursor-pointer hover:border-violet-600 transition-all"
                          onClick={() => fetchLegalRef('sancion', String(s.id))}
                          title="Click para ver detalle completo"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-violet-300 font-semibold">{s.entidad}</span>
                            <span className="text-rose-400 font-mono font-bold">{s.multa_total_uit} UIT</span>
                          </div>
                          <p className="text-slate-400 text-[10px] mt-0.5 font-mono">{s.resolucion}</p>
                          {s.infracciones && s.infracciones.slice(0, 1).map((inf, j) => (
                            <p key={j} className="text-slate-500 text-[10px] mt-0.5 truncate">{inf}</p>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* CONSOLA DE AUDITORÍA & REMEDIACIÓN (DeepSeek v4.1 Flash) */}
            <div className="glass-card p-4 border-slate-800 flex-1 flex flex-col min-h-[460px]">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800 mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 "></div>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">Auditor de Cumplimiento & DSPM (ISO/IEC 27701 & Ley 29733)</h4>
                </div>
                <span className="text-[10px] text-cyan-400 font-mono">{status?.llm_model ? `${status.llm_model} (OpenRouter)` : "Auditor IA (OpenRouter)"}</span>
                  {selectedFinding && (
                    <button 
                      onClick={() => handleExportDictamen(selectedFinding)}
                      title="Descargar dictamen pericial completo en Markdown"
                      className="inline-flex items-center gap-1 px-2 py-0.5 ml-2 rounded bg-cyan-950/80 hover:bg-cyan-900 text-[10px] font-medium text-cyan-300 border border-cyan-800 transition-colors shadow-sm"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                      Dictamen .MD
                    </button>
                  )}
              </div>

              {/* Mensajes del chat */}
              <div className="flex-1 overflow-y-auto pr-1.5 flex flex-col gap-3 mb-3 max-h-[480px] min-h-[320px]">
                {chatHistory.map((m, idx) => (
                  <div key={idx} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                    {/* Accordion de Reasoning */}
                    {m.reasoning && (
                      <details className="mb-1.5 w-full text-[11px] bg-slate-950/90 rounded-lg p-2 border border-slate-800 text-slate-400">
                        <summary className="cursor-pointer font-semibold text-cyan-400 flex items-center gap-1.5 hover:text-cyan-300">
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                          Cadena de razonamiento pericial
                        </summary>
                        <div className="mt-2 text-slate-400 font-mono text-[10px] whitespace-pre-wrap leading-relaxed border-t border-slate-800/80 pt-2">
                          {m.reasoning}
                        </div>
                      </details>
                    )}

                                        <div className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-zinc-800 text-zinc-100 border border-zinc-700/70 rounded-tr-none max-w-[85%] shadow-md ml-auto'
                        : 'bg-zinc-950/90 text-zinc-200 border border-zinc-800 rounded-tl-none max-w-[95%] shadow-md'
                    }`}>
                      {m.role === 'user' ? (
                        <div className="whitespace-pre-wrap font-medium">{m.content}</div>
                      ) : (
                        <div
                          className="chat-markdown"
                          dangerouslySetInnerHTML={{
                            __html: formatMarkdownCitations(m.content)
                          }}
                        />
                      )}
                    </div>

                    {chatLoading && (
                      <div className="flex items-center gap-2 p-3 rounded-2xl bg-zinc-950/90 border border-zinc-800 text-xs text-slate-400">
                        <div className="w-3.5 h-3.5 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin"></div>
                        <span>Generando dictamen pericial...</span>
                      </div>
                    )}

                    {/* SQL Patch Card */}
                    {m.sql_patch && (
                      <div className="w-full mt-2 p-3 bg-[#060911] border border-cyan-800/60 rounded-xl">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[10px] font-bold text-cyan-300 font-mono flex items-center gap-1">
                            <svg className="w-3 h-3 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>
                            Código de Remediación
                          </span>
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(m.sql_patch);
                                showToast("Código copiado al portapapeles.", "success");
                              }}
                              className="text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-700"
                            >
                              Copiar
                            </button>
                            <button
                              onClick={handleRemediate}
                              className="text-[10px] bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-2 py-0.5 rounded"
                            >
                              Marcar Resuelto
                            </button>
                          </div>
                        </div>
                        <pre className="text-[11px] font-mono text-cyan-200 overflow-x-auto p-2 bg-slate-950 rounded border border-slate-900 leading-tight">
                          <code>{m.sql_patch}</code>
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
                <div ref={chatBottomRef} />
              </div>

              {/* Input de chat */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Consulta al Auditor: diagnóstico, remediación, precedentes ANPD, fundamento legal...'Genera parche SQL', 'Fundamento legal')..."
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
                <button
                  type="submit"
                  disabled={loading || !chatInput.trim()}
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-bold text-xs shadow-md shadow-cyan-600/20"
                >
                  Enviar
                </button>
              </form>
            </div>

          </div>

        </main>
      )}

      {/* REACT CONFIRMATION MODAL (Replaces browser window.confirm) */}
      {confirmModal.open && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card max-w-md w-full p-6 border border-slate-700 shadow-2xl animate-scale-up">
            <h3 className="text-base font-bold text-white mb-2">{confirmModal.title}</h3>
            <p className="text-xs text-slate-300 mb-6 leading-relaxed">{confirmModal.message}</p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setConfirmModal({ open: false })}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
              >
                Cancelar
              </button>
              <button
                onClick={confirmModal.onConfirm}
                className={`px-4 py-2 rounded-xl text-xs font-bold text-white shadow-lg ${confirmModal.confirmColor || 'bg-cyan-600 hover:bg-cyan-500'}`}
              >
                {confirmModal.confirmText || 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SPINNER OVERLAY */}
      {loading && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
          <div className="w-12 h-12 rounded-full border-4 border-cyan-500 border-t-transparent animate-spin mb-3"></div>
          <p className="text-xs font-semibold text-slate-200">{loadingMsg || 'Procesando...'}</p>
        </div>
      )}

      {/* MODAL DE REFERENCIA LEGAL */}
      {legalRefModal.open && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setLegalRefModal({ open: false })}>
          <div className="glass-card max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6 border border-slate-700 shadow-2xl animate-scale-up" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                {legalRefModal.tipo === 'control' && 'Control ISO/IEC 27701:2025'}
                {legalRefModal.tipo === 'articulo' && 'Ley N.° 29733 - Protección de Datos Personales'}
                {legalRefModal.tipo === 'sancion' && 'Precedente Sancionador ANPD'}
              </h3>
              <button onClick={() => setLegalRefModal({ open: false })} className="text-slate-400 hover:text-white text-lg">✕</button>
            </div>
            
            {legalRefModal.loading && (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin"></div>
                <span className="ml-2 text-xs text-slate-400">Cargando referencia...</span>
              </div>
            )}
            
            {legalRefModal.data && !legalRefModal.loading && (
              <div className="space-y-3 text-xs">
                {legalRefModal.data.error && (
                  <p className="text-rose-400">{legalRefModal.data.error}</p>
                )}
                
                {/* CONTROL ISO */}
                {legalRefModal.tipo === 'control' && legalRefModal.data.data && (
                  <>
                    <div className="bg-slate-900 rounded-lg p-3 border border-slate-800">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-mono text-cyan-400 font-bold text-sm">{legalRefModal.data.data.id}</span>
                        <span className="text-[10px] bg-cyan-950 text-cyan-300 px-2 py-0.5 rounded-full border border-cyan-800">{legalRefModal.data.data.role}</span>
                      </div>
                      <h4 className="text-white font-semibold mb-1">{legalRefModal.data.data.title}</h4>
                      <p className="text-slate-400 text-[11px]">Categoría: {legalRefModal.data.data.category}</p>
                    </div>
                    
                    {legalRefModal.data.data.peru_legal_bridge && (
                      <div className="bg-emerald-950/40 rounded-lg p-3 border border-emerald-800/50">
                        <h5 className="text-emerald-400 font-bold text-[11px] mb-2">Mapeo Legal Peruano</h5>
                        <div className="space-y-1.5">
                          <p className="text-slate-300"><span className="text-emerald-400 font-medium">Ley 29733:</span> {legalRefModal.data.data.peru_legal_bridge.ley_29733}</p>
                          <p className="text-slate-300"><span className="text-emerald-400 font-medium">D.S. 003-2013:</span> {legalRefModal.data.data.peru_legal_bridge.ds_003_2013_jus}</p>
                          <p className="text-slate-300"><span className="text-emerald-400 font-medium">Directiva:</span> {legalRefModal.data.data.peru_legal_bridge.directiva_seguridad}</p>
                        </div>
                      </div>
                    )}
                    
                    {legalRefModal.data.principios_vinculados && legalRefModal.data.principios_vinculados.length > 0 && (
                      <div className="bg-violet-950/30 rounded-lg p-3 border border-violet-800/40">
                        <h5 className="text-violet-400 font-bold text-[11px] mb-2">Principios ISO 29100 Vinculados</h5>
                        {legalRefModal.data.principios_vinculados.map((p, i) => (
                          <p key={i} className="text-slate-300 text-[11px] mb-1">• {p.name || p.id}: {p.ley_29733_principle || ''}</p>
                        ))}
                      </div>
                    )}
                  </>
                )}
                
                {/* ARTÍCULO LEY 29733 */}
                {legalRefModal.tipo === 'articulo' && legalRefModal.data.data && (
                  <div className="bg-slate-900 rounded-lg p-4 border border-slate-800">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="font-mono text-emerald-400 font-bold">Art. {legalRefModal.data.data.articulo}</span>
                      <span className="text-white font-semibold">{legalRefModal.data.data.titulo}</span>
                    </div>
                    <p className="text-slate-300 leading-relaxed whitespace-pre-wrap text-[11px]">{legalRefModal.data.data.texto}</p>
                  </div>
                )}
                
                {/* SANCIÓN ANPD */}
                {legalRefModal.tipo === 'sancion' && legalRefModal.data.data && (
                  <>
                    <div className="bg-slate-900 rounded-lg p-3 border border-slate-800">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-white font-bold">{legalRefModal.data.data.entidad}</span>
                        <span className="text-rose-400 font-mono font-bold">{legalRefModal.data.data.multa_total_uit} UIT</span>
                      </div>
                      <p className="text-slate-400 text-[11px]">Sector: {legalRefModal.data.data.sector}</p>
                      {legalRefModal.data.data.resoluciones && legalRefModal.data.data.resoluciones.map((r, i) => (
                        <p key={i} className="text-cyan-400 text-[11px] font-mono mt-1">{r}</p>
                      ))}
                    </div>
                    
                    {legalRefModal.data.data.infracciones && legalRefModal.data.data.infracciones.length > 0 && (
                      <div className="bg-rose-950/30 rounded-lg p-3 border border-rose-800/40">
                        <h5 className="text-rose-400 font-bold text-[11px] mb-2">Infracciones Tipificadas</h5>
                        {legalRefModal.data.data.infracciones.map((inf, i) => (
                          <div key={i} className="text-slate-300 text-[11px] mb-2 pl-2 border-l-2 border-rose-800/50">
                            {typeof inf === 'object' ? (
                              <><span className="text-rose-300 font-medium">{inf.articulo_referencia}:</span> {inf.texto_infraccion}</>
                            ) : inf}
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {legalRefModal.data.data.medidas_correctivas && legalRefModal.data.data.medidas_correctivas.length > 0 && (
                      <div className="bg-amber-950/30 rounded-lg p-3 border border-amber-800/40">
                        <h5 className="text-amber-400 font-bold text-[11px] mb-2">Medidas Correctivas Ordenadas</h5>
                        {legalRefModal.data.data.medidas_correctivas.map((m, i) => (
                          <p key={i} className="text-slate-300 text-[11px] mb-1">• {m}</p>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TOAST NOTIFICATION */}
      {toast && (
        <div className={`fixed bottom-5 right-5 z-50 max-w-sm glass-card p-3.5 border shadow-2xl flex items-center gap-2.5 text-xs animate-slide-up ${
          toast.type === 'success' ? 'border-emerald-500 text-emerald-200' :
          toast.type === 'error' ? 'border-rose-500 text-rose-200' :
          'border-cyan-500 text-cyan-200'
        }`}>
          <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
