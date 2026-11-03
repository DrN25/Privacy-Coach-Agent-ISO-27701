// ==============================================================================
// SISTEMA DE AUDITORÍA DSPM & GESTOR DE BRECHAS PII (ISO 27701 & LEY 29733)
// Interfaz de Peritaje Forense Institucional • No-AI-Slop Architecture
// ==============================================================================

if (window.marked) {
  window.marked.setOptions({
    gfm: true,
    breaks: true
  });
}

// Puente global para citas legales interactivas
window.fetchLegalRefGlobal = function(tipo, refId) {
  if (window.__triggerLegalRefModal) {
    window.__triggerLegalRefModal(tipo, refId);
  } else {
    console.warn("fetchLegalRefGlobal: React App no enlazada aún:", tipo, refId);
  }
};

const { useState, useEffect, useMemo, useRef } = React;

// ==============================================================================
// ICONOGRAFÍA VECTORIAL ESPECÍFICA (SIN EMOJIS, LÍNEA SOBRIA 1.5PX)
// ==============================================================================

function IconShield({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function IconFolder({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z" />
    </svg>
  );
}

function IconFileText({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <line x1="10" y1="9" x2="8" y2="9" />
    </svg>
  );
}

function IconSearch({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function IconExternalLink({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  );
}

function IconDownload({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

function IconTrash({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

function IconCheck({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function IconX({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function IconUpload({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

function IconCpu({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <rect x="9" y="9" width="6" height="6" />
      <line x1="9" y1="1" x2="9" y2="4" />
      <line x1="15" y1="1" x2="15" y2="4" />
      <line x1="9" y1="20" x2="9" y2="23" />
      <line x1="15" y1="20" x2="15" y2="23" />
      <line x1="20" y1="9" x2="23" y2="9" />
      <line x1="20" y1="14" x2="23" y2="14" />
      <line x1="1" y1="9" x2="4" y2="9" />
      <line x1="1" y1="14" x2="4" y2="14" />
    </svg>
  );
}

function IconSend({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function IconMessageSquare({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

// ==============================================================================
// COMPONENTE PRINCIPAL
// ==============================================================================

function App() {
  // Navegación principal de módulos: 'expedientes' | 'repositorio'
  const [activeModule, setActiveModule] = useState('expedientes');
  
  // Tema visual institucional (3 variantes Sillar Claro)
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('pims_unsa_theme');
    if (saved === 'sillar') return 'sillar-lacre';
    return saved || 'sillar-lacre';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('pims_unsa_theme', theme);
  }, [theme]);

  // Drawer lateral del Consultor DPO / Chatbot
  const [chatDrawerOpen, setChatDrawerOpen] = useState(false);

  // Datos del backend
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loadedDocuments, setLoadedDocuments] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  
  // Filtros
  const [searchIncident, setSearchIncident] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'OPEN' | 'RESOLVED'
  const [searchDoc, setSearchDoc] = useState('');

  // Modales
  const [inspectDocModal, setInspectDocModal] = useState({ open: false, loading: false, data: null });
  const [legalModal, setLegalModal] = useState({ open: false, loading: false, tipo: '', data: null });
  const [confirmModal, setConfirmModal] = useState({ open: false, title: '', message: '', danger: false, onConfirm: null });
  
  // Consultor DPO y Chat
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [expandedFlows, setExpandedFlows] = useState({});
  const [uploading, setUploading] = useState(false);

  const toggleFlowMessage = (index) => {
    setExpandedFlows(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // Notificaciones Toast
  const [toast, setToast] = useState({ visible: false, message: '', type: 'info' });

  const fileInputRef = useRef(null);
  const chatBottomRef = useRef(null);

  const showToast = (message, type = 'info') => {
    setToast({ visible: true, message, type });
    setTimeout(() => setToast(prev => ({ ...prev, visible: false })), 4500);
  };

  // Enlace para citas normativas
  useEffect(() => {
    const handler = (tipo, refId) => {
      fetchLegalReference(tipo, refId);
    };
    window.fetchLegalRefGlobal = handler;
    window.__triggerLegalRefModal = handler;
    return () => {
      window.fetchLegalRefGlobal = null;
      window.__triggerLegalRefModal = null;
    };
  }, []);

  // Carga inicial de datos
  useEffect(() => {
    fetchStatus();
    fetchIncidents();
    fetchDocumentsCorpus();
    fetchLoadedDocuments();
  }, []);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, chatLoading]);

  // Sincronizar chat inicial al seleccionar incidente
  useEffect(() => {
    if (selectedIncident) {
      setChatMessages([
        {
          role: 'assistant',
          content: `**Expediente Activo:** \`${selectedIncident.incident_code}\`  \n**Sistema Auditado:** ${selectedIncident.compromised_system}  \n**Instrumento de Origen:** \`${selectedIncident.documento_fuente_pdf || 'Normativa institucional'}\`  \n**Norma Primaria:** [Ref: ISO 27701 ${selectedIncident.regla?.control_iso27701 || 'A.3.24'}] y [Ley 29733 Art. ${selectedIncident.regla?.articulo_lpdp || '28'}].\n\n¿Desea evaluar el nexo causal de esta brecha, revisar la cuantía en UIT (${selectedIncident.multa_estimada_uit || 12.5} UIT) o consultar los precedentes sancionadores de la ANPD?`,
          provenance: 'local',
          trazabilidad: [
            { agente: 'Supervisor', estado: 'ok', accion: `Inicialización de expediente ${selectedIncident.incident_code}` },
            { agente: 'Context Agent', estado: 'ok', accion: `Carga de activo ${selectedIncident.compromised_system}` },
            { agente: 'DSPM Risk Engine', estado: 'ok', accion: `Cuantía preliminar de ${selectedIncident.multa_estimada_uit || 12.5} UIT` },
            { agente: 'Normative Agent', estado: 'ok', accion: `Enlace normativo ISO 27701 (${selectedIncident.regla?.control_iso27701 || 'A.3.24'}) y Ley 29733` },
            { agente: 'Oficial DPO', estado: 'ok', accion: 'Canal pericial interactivo activo' }
          ]
        }
      ]);
    }
  }, [selectedIncident?.id]);

  // ============================================================================
  // SERVICIOS API
  // ============================================================================

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status');
      if (res.ok) setSystemStatus(await res.json());
    } catch (e) {
      console.warn("Estado backend no disponible:", e);
    }
  };

  const fetchIncidents = async () => {
    try {
      const res = await fetch('/api/incidents');
      if (res.ok) {
        const data = await res.json();
        const list = data.incidents || data.incidentes || [];
        setIncidents(list);
        if (list.length > 0 && !selectedIncident) {
          fetchIncidentDetail(list[0].id);
        }
      }
    } catch (e) {
      showToast('No se pudo conectar con el registro de incidentes', 'error');
    }
  };

  const fetchIncidentDetail = async (id) => {
    try {
      const res = await fetch(`/api/incidents/${id}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedIncident(data);
      }
    } catch (e) {
      showToast('Error al obtener expediente', 'error');
    }
  };

  const fetchDocumentsCorpus = async () => {
    try {
      const res = await fetch('/api/mockups');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.mockups || []);
      }
    } catch (e) {
      console.warn("Error al listar documentos:", e);
    }
  };

  const fetchLoadedDocuments = async () => {
    try {
      const res = await fetch('/api/database-view');
      if (res.ok) {
        const data = await res.json();
        setLoadedDocuments(data.archivos || []);
      }
    } catch (e) {
      console.warn("Error al obtener archivos indexados:", e);
    }
  };

  const handleCloseIncident = async (incidentId) => {
    setConfirmModal({
      open: true,
      title: 'Cierre Formal de Expediente de Brecha',
      message: `¿Confirma el cierre formal del expediente INC-UNSA-${incidentId}? El estado se actualizará a RESUELTO en el registro institucional y se registrará al auditor responsable.`,
      danger: false,
      onConfirm: async () => {
        try {
          const res = await fetch(`/api/incidents/${incidentId}/close`, { method: 'POST' });
          if (res.ok) {
            showToast(`Expediente INC-UNSA-${incidentId} cerrado formalmente.`, 'success');
            await fetchIncidents();
            await fetchIncidentDetail(incidentId);
          } else {
            showToast('No se pudo completar el cierre del expediente.', 'error');
          }
        } catch (e) {
          showToast('Error de conexión al cerrar expediente', 'error');
        } finally {
          setConfirmModal({ open: false, title: '', message: '', onConfirm: null });
        }
      }
    });
  };

  const handleExportDictamen = (incidentId) => {
    window.open(`/api/incidents/${incidentId}/export-dictamen`, '_blank');
  };

  const handleUploadDocument = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    showToast(`Procesando '${file.name}' con OCR y AST...`, 'info');

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        showToast(`Documento '${file.name}' incorporado al inventario activo.`, 'success');
        await Promise.all([fetchDocumentsCorpus(), fetchLoadedDocuments(), fetchIncidents()]);
      } else {
        const err = await res.json();
        showToast(err.detail || 'Error al procesar el archivo', 'error');
      }
    } catch (err) {
      showToast('Error de red al subir el documento', 'error');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleExcludeDocument = (archivoId, nombreArchivo) => {
    setConfirmModal({
      open: true,
      title: 'Excluir Instrumento del Alcance Activo',
      message: `¿Desea excluir '${nombreArchivo}' del inventario de auditoría? Se desvincularán sus cláusulas y columnas sensibles.`,
      danger: true,
      onConfirm: async () => {
        try {
          const res = await fetch(`/api/documents/${archivoId}`, { method: 'DELETE' });
          if (res.ok) {
            showToast(`Instrumento '${nombreArchivo}' excluido.`, 'info');
            await Promise.all([fetchLoadedDocuments(), fetchDocumentsCorpus()]);
            if (inspectDocModal.open && inspectDocModal.data?.archivo?.id === archivoId) {
              setInspectDocModal({ open: false, loading: false, data: null });
            }
          }
        } catch (e) {
          showToast('Error al excluir el documento', 'error');
        } finally {
          setConfirmModal({ open: false, title: '', message: '', onConfirm: null });
        }
      }
    });
  };

  const handleInspectDocument = async (archivoIdOrName) => {
    setInspectDocModal({ open: true, loading: true, data: null });
    try {
      const res = await fetch(`/api/documents/${encodeURIComponent(archivoIdOrName)}/preview`);
      if (res.ok) {
        const data = await res.json();
        setInspectDocModal({ open: true, loading: false, data });
        if (!documents.some(d => d.id === data?.archivo?.id)) {
          fetchLoadedDocuments();
          fetchDocumentsCorpus();
        }
      } else {
        showToast('No se pudo cargar la vista previa del instrumento', 'error');
        setInspectDocModal({ open: false, loading: false, data: null });
      }
    } catch (e) {
      showToast('Error al inspeccionar documento', 'error');
      setInspectDocModal({ open: false, loading: false, data: null });
    }
  };

  const fetchLegalReference = async (tipo, refId) => {
    setLegalModal({ open: true, loading: true, tipo, data: null });
    try {
      const res = await fetch(`/api/legal-reference/${tipo}/${encodeURIComponent(refId)}`);
      if (res.ok) {
        const data = await res.json();
        setLegalModal({ open: true, loading: false, tipo, data });
      } else {
        showToast('Referencia legal no encontrada en el corpus normativo', 'error');
        setLegalModal({ open: false, loading: false, tipo, data: null });
      }
    } catch (e) {
      showToast('Error al consultar referencia legal', 'error');
      setLegalModal({ open: false, loading: false, tipo, data: null });
    }
  };

  const handleSendChat = async (promptTexto) => {
    const texto = (promptTexto || chatInput).trim();
    if (!texto || chatLoading) return;

    const nuevoMsgUser = { role: 'user', content: texto };
    setChatMessages(prev => [...prev, nuevoMsgUser]);
    if (!promptTexto) setChatInput('');
    setChatLoading(true);

    try {
      const payload = {
        hallazgo_id: selectedIncident?.id || 1,
        mensaje: texto,
        mensaje_usuario: texto,
        historial: chatMessages.slice(-6).map(m => ({ role: m.role, content: m.content }))
      };

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setChatMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: data.mensaje || data.respuesta || 'Dictamen pericial emitido.',
            provenance: data.mode || (data.contexto_unsa?.a2a_disponible ? 'a2a' : 'local'),
            trazabilidad: data.trazabilidad || [],
            reasoning: data.reasoning || '',
            sql_patch: data.sql_patch || '',
            citas: data.citas || []
          }
        ]);
      } else {
        const errData = await res.json().catch(() => ({}));
        showToast(errData.detail || 'Error al consultar al motor pericial', 'error');
      }
    } catch (err) {
      showToast('Error de comunicación con el consultor', 'error');
    } finally {
      setChatLoading(false);
      setTimeout(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  };

  // Filtrado de incidentes
  const filteredIncidents = useMemo(() => {
    return incidents.filter(inc => {
      const matchSearch = !searchIncident || 
        inc.title?.toLowerCase().includes(searchIncident.toLowerCase()) ||
        inc.incident_code?.toLowerCase().includes(searchIncident.toLowerCase()) ||
        inc.compromised_system?.toLowerCase().includes(searchIncident.toLowerCase());

      const matchStatus = 
        statusFilter === 'ALL' ? true :
        statusFilter === 'OPEN' ? inc.status !== 'RESUELTO' :
        inc.status === 'RESUELTO';

      return matchSearch && matchStatus;
    });
  }, [incidents, searchIncident, statusFilter]);

  // Filtrado de documentos
  const filteredDocs = useMemo(() => {
    return documents.filter(doc => {
      return !searchDoc ||
        doc.nombre?.toLowerCase().includes(searchDoc.toLowerCase()) ||
        doc.descripcion?.toLowerCase().includes(searchDoc.toLowerCase());
    });
  }, [documents, searchDoc]);

  // Renderizador de Markdown con citas interactivas profesionales (sin emojis ni colisiones)
  const renderLegalMarkdown = (text) => {
    if (!text) return '';
    // Sanitizar posibles fragmentos de HTML corrupto previo o emojis
    let clean = text
      .replace(/<button[^>]*>.*?<\/button>/gi, '')
      .replace(/[📜⚖️]/gu, '');

    // Paso 1: Convertir referencias normativas a tokens únicos seguros
    let processed = clean
      .replace(/\[(?:Ref:\s*)?ISO\s*27701\s*([0-9a-zA-Z\.]+)\]/gi, '@@@TOKEN_ISO_$1@@@')
      .replace(/\[(?:Ref:\s*)?Ley\s*29733\s*Art\.?\s*([0-9\w\-]+)\]/gi, '@@@TOKEN_LEY_$1@@@')
      .replace(/\bISO(?:\/IEC)?\s*27701(?:\s*:\s*2025)?\s+(?:control\s+)?([A-Za-z]\.[0-9]+(?:\.[0-9]+)?)\b/gi, '@@@TOKEN_ISO_$1@@@')
      .replace(/\bLey\s*(?:N°\s*)?29733(?:\s*,\s*|\s+)Art(?:ículo|\.)?\s*([0-9\w\-]+)\b/gi, '@@@TOKEN_LEY_$1@@@')
      .replace(/\bArt(?:ículo|\.)?\s*([0-9\w\-]+)\s+de\s+la\s+Ley\s*(?:N°\s*)?29733\b/gi, '@@@TOKEN_LEY_$1@@@');

    // Paso 2: Reemplazar tokens con botones tipográficos limpios y accesibles
    processed = processed
      .replace(/@@@TOKEN_ISO_([0-9a-zA-Z\.]+)@@@/g, (m, p) => {
        return `<button type="button" onclick="window.fetchLegalRefGlobal('iso27701', '${p}')" class="inline-flex items-center px-1.5 py-0.5 rounded bg-rose-50 hover:bg-rose-100 text-rose-900 border border-rose-300 text-xs font-mono font-semibold cursor-pointer transition-colors shadow-2xs mx-0.5" title="Ver control ISO/IEC 27701 ${p}">ISO 27701 ${p}</button>`;
      })
      .replace(/@@@TOKEN_LEY_([0-9\w\-]+)@@@/g, (m, p) => {
        return `<button type="button" onclick="window.fetchLegalRefGlobal('ley29733', '${p}')" class="inline-flex items-center px-1.5 py-0.5 rounded bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 text-xs font-mono font-semibold cursor-pointer transition-colors shadow-2xs mx-0.5" title="Ver Artículo ${p} de la Ley N° 29733">Ley 29733 Art. ${p}</button>`;
      });

    if (window.marked) {
      return { __html: window.marked.parse(processed) };
    }
    return { __html: processed };
  };

  return (
    <div className="min-h-screen flex flex-col bg-surface-ground text-ink-primary font-sans relative">
      
      {/* ==================================================================== */}
      {/* 1. CABECERA INSTITUCIONAL Y SELECTOR DE MÓDULOS                      */}
      {/* ==================================================================== */}
      <header className="h-14 app-header px-5 flex items-center justify-between shrink-0 select-none shadow-xs">
        
        {/* Identidad de la Plataforma */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-white/15 text-white font-serif font-bold text-sm flex items-center justify-center border border-white/20 shadow-xs">
              U
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-serif font-bold text-sm text-white tracking-tight">
                  SISTEMA DE AUDITORÍA DSPM & GESTOR DE BRECHAS PII
                </span>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-white/15 text-white/90 border border-white/20">
                  ISO 27701 • LEY 29733
                </span>
              </div>
              <div className="text-[11px] text-white/80">
                Entidad Auditada: <strong className="text-white font-semibold">Universidad Nacional de San Agustín de Arequipa (UNSA)</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Selector de Módulos Principales (Desacoplado y Evidente) */}
        <div className="flex items-center gap-1 bg-black/20 p-1 rounded border border-white/15">
          <button
            onClick={() => setActiveModule('expedientes')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors inline-flex items-center gap-1.5 ${
              activeModule === 'expedientes'
                ? 'bg-white text-slate-900 font-bold shadow-xs'
                : 'text-white/80 hover:text-white'
            }`}
          >
            <IconShield className="w-3.5 h-3.5" />
            <span>Expedientes de Brechas ({incidents.length})</span>
          </button>

          <button
            onClick={() => setActiveModule('repositorio')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-colors inline-flex items-center gap-1.5 ${
              activeModule === 'repositorio'
                ? 'bg-white text-slate-900 font-bold shadow-xs'
                : 'text-white/80 hover:text-white'
            }`}
          >
            <IconFolder className="w-3.5 h-3.5" />
            <span>Repositorio de Instrumentos ({documents.length})</span>
          </button>
        </div>

        {/* Acciones, Variantes Sillar Claro y Copilot Trigger */}
        <div className="flex items-center gap-2.5">
          
          {/* Selector de 3 Variantes Sillar Claro */}
          <div className="flex items-center gap-1 bg-black/20 p-1 rounded border border-white/15">
            <button
              onClick={() => setTheme('sillar-lacre')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-all inline-flex items-center gap-1.5 ${
                theme === 'sillar-lacre' || theme === 'sillar'
                  ? 'bg-white text-slate-900 font-bold shadow-xs'
                  : 'text-white/80 hover:text-white'
              }`}
              title="Variante 1: Sillar Lacre Cardenal UNSA (Heráldico)"
            >
              <span className="w-2.5 h-2.5 rounded-full bg-[#881337] border border-white/80 shadow-2xs"></span>
              <span>Lacre Cardenal</span>
            </button>

            <button
              onClick={() => setTheme('sillar-cobalto')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-all inline-flex items-center gap-1.5 ${
                theme === 'sillar-cobalto'
                  ? 'bg-white text-slate-900 font-bold shadow-xs'
                  : 'text-white/80 hover:text-white'
              }`}
              title="Variante 2: Sillar Cobalto Forense & DSPM (Gobernanza)"
            >
              <span className="w-2.5 h-2.5 rounded-full bg-[#0284c7] border border-white/80 shadow-2xs"></span>
              <span>Cobalto Pericial</span>
            </button>

            <button
              onClick={() => setTheme('sillar-terracota')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-all inline-flex items-center gap-1.5 ${
                theme === 'sillar-terracota'
                  ? 'bg-white text-slate-900 font-bold shadow-xs'
                  : 'text-white/80 hover:text-white'
              }`}
              title="Variante 3: Sillar Terracota Andino & Olivo (Editorial)"
            >
              <span className="w-2.5 h-2.5 rounded-full bg-[#c2410c] border border-white/80 shadow-2xs"></span>
              <span>Terracota Andino</span>
            </button>
          </div>

          <label className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-white/10 hover:bg-white/20 border border-white/20 cursor-pointer transition-colors text-xs font-medium text-white">
            <IconUpload className="w-3.5 h-3.5" />
            <span>{uploading ? "Indexando..." : "Cargar Instrumento"}</span>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".pdf,.sql,.md,.txt" 
              onChange={handleUploadDocument}
              disabled={uploading}
            />
          </label>

          <button
            onClick={() => setChatDrawerOpen(prev => !prev)}
            className={`px-3 py-1.5 rounded text-xs font-medium inline-flex items-center gap-1.5 border transition-colors ${
              chatDrawerOpen
                ? 'bg-white text-slate-900 font-bold border-white shadow-sm'
                : 'bg-white/10 hover:bg-white/20 text-white border-white/20'
            }`}
            title="Abrir Asistente DPO y Jurisprudencia ANPD"
          >
            <IconMessageSquare className="w-3.5 h-3.5" />
            <span>Consultor DPO</span>
          </button>
        </div>
      </header>

      {/* ==================================================================== */}
      {/* 2. ESPACIO DE TRABAJO DINÁMICO                                       */}
      {/* ==================================================================== */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* ================================================================== */}
        {/* VISTA A: EXPEDIENTES DE BRECHAS (SPLIT-VIEW DE ALTA DENSIDAD)      */}
        {/* ================================================================== */}
        {activeModule === 'expedientes' && (
          <>
            {/* Lista Lateral de Expedientes */}
            <aside className="w-full md:w-[350px] border-r border-surface-border bg-surface-sidebar flex flex-col shrink-0">
              <div className="p-3 border-b border-surface-border space-y-2">
                <div className="relative">
                  <IconSearch className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-ink-muted" />
                  <input
                    type="text"
                    value={searchIncident}
                    onChange={(e) => setSearchIncident(e.target.value)}
                    placeholder="Filtrar por código o sistema..."
                    className="w-full bg-surface-ground border border-surface-border rounded pl-8 pr-3 py-1.5 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-unsa-700"
                  />
                </div>
                
                <div className="flex items-center gap-1 text-[11px] font-mono">
                  {['ALL', 'OPEN', 'RESOLVED'].map(st => (
                    <button
                      key={st}
                      onClick={() => setStatusFilter(st)}
                      className={`px-2 py-0.5 rounded transition-colors ${
                        statusFilter === st
                          ? 'bg-unsa-800 text-white font-semibold'
                          : 'text-ink-secondary hover:bg-surface-card'
                      }`}
                    >
                      {st === 'ALL' ? 'Todos' : st === 'OPEN' ? 'Abiertos' : 'Resueltos'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Listado de Casos */}
              <div className="flex-1 overflow-y-auto divide-y divide-surface-border">
                {filteredIncidents.map(inc => {
                  const isSelected = selectedIncident?.id === inc.id;
                  const isClosed = inc.status === 'RESUELTO';
                  
                  return (
                    <div
                      key={inc.id}
                      onClick={() => fetchIncidentDetail(inc.id)}
                      className={`p-3.5 cursor-pointer transition-all border-l-3 ${
                        isSelected
                          ? 'bg-[var(--active-card-bg)] border-l-[var(--active-card-border)] shadow-xs'
                          : 'hover:bg-surface-elevated border-l-transparent'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono text-[11px] font-bold text-ink-primary">
                          {inc.incident_code}
                        </span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                          isClosed
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold'
                            : inc.severity === 'CRÍTICA' || inc.severity === 'MUY GRAVE'
                            ? 'bg-rose-50 text-rose-800 border-rose-300 font-bold'
                            : 'bg-amber-50 text-amber-800 border-amber-300 font-semibold'
                        }`}>
                          {isClosed ? 'RESUELTO' : inc.severity || 'ALTA'}
                        </span>
                      </div>

                      <div className="text-xs font-medium text-ink-primary line-clamp-2 mb-1 leading-snug">
                        {inc.title}
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-ink-muted font-mono">
                        <span className="truncate max-w-[180px]">{inc.compromised_system || 'Sistema UNSA'}</span>
                        <span className="text-[var(--unsa-primary)] font-bold shrink-0">
                          {inc.multa_estimada_uit ? `${inc.multa_estimada_uit} UIT` : 'Sanción'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </aside>

            {/* Dossier Pericial Integral (Llena el espacio con evidencia real y remediación) */}
            <main className="flex-1 overflow-y-auto bg-surface-ground p-6">
              {selectedIncident ? (
                <div className="max-w-5xl mx-auto space-y-6">
                  
                  {/* Encabezado del Dossier */}
                  <div className="p-5 rounded border border-surface-border bg-surface-card flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-[var(--unsa-badge-bg)] text-[var(--unsa-badge-text)] border border-[var(--unsa-badge-border)]">
                          {selectedIncident.incident_code}
                        </span>
                        <span className={`text-[10px] font-mono px-2.5 py-0.5 rounded border ${
                          selectedIncident.status === 'RESUELTO'
                            ? 'bg-emerald-50 text-emerald-900 border-emerald-300 font-bold'
                            : 'bg-rose-50 text-rose-900 border-rose-300 font-bold'
                        }`}>
                          {selectedIncident.status === 'RESUELTO' ? 'EXPEDIENTE RESUELTO' : 'EN INVESTIGACIÓN PERICIAL'}
                        </span>
                        <span className="text-xs text-ink-muted font-mono font-medium">
                          {selectedIncident.compromised_system}
                        </span>
                      </div>
                      
                      <h1 className="font-serif font-bold text-lg text-ink-primary leading-snug">
                        {selectedIncident.title}
                      </h1>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleExportDictamen(selectedIncident.id)}
                        className="px-3.5 py-1.5 rounded bg-white hover:bg-slate-100 text-slate-800 hover:text-slate-950 border border-slate-300 text-xs font-semibold inline-flex items-center gap-1.5 transition-colors shadow-2xs"
                        title="Exportar Dictamen Pericial Oficial bajo ISO/IEC 27035 y Ley 29733"
                      >
                        <IconDownload className="w-3.5 h-3.5 text-slate-700" />
                        <span>Dictamen Oficial (.txt)</span>
                      </button>

                      {selectedIncident.status !== 'RESUELTO' && (
                        <button
                          onClick={() => handleCloseIncident(selectedIncident.id)}
                          className="px-3.5 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] text-white text-xs font-semibold inline-flex items-center gap-1.5 transition-colors shadow-xs"
                        >
                          <IconCheck className="w-3.5 h-3.5" />
                          <span>Cerrar Expediente</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* BLOQUE 1: EVIDENCIA DOCUMENTAL Y TRAZABILIDAD FÍSICA (Resuelve 'parece inventado') */}
                  <div className="p-5 rounded border border-surface-border bg-surface-card space-y-4">
                    <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
                      <div className="flex items-center gap-2">
                        <IconFileText className="w-4 h-4 text-[var(--unsa-primary)]" />
                        <span className="font-serif font-bold text-sm text-ink-primary">
                          Instrumentos Documentales y Evidencia de Respaldo en Custodia
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-ink-muted">
                        Trazabilidad Verificada en Disco
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Documento PDF Fuente */}
                      {selectedIncident.documento_fuente_pdf && (
                        <div className="p-3.5 bg-surface-ground rounded border border-surface-border space-y-2">
                          <div className="text-[10px] font-mono text-ink-muted uppercase tracking-wider font-semibold">
                            Normativa / Reglamento Oficial Afectado
                          </div>
                          <div className="font-semibold text-xs text-ink-primary">
                            {selectedIncident.descripcion_documento || selectedIncident.documento_fuente_pdf}
                          </div>
                          <div className="font-mono text-[11px] text-ink-secondary truncate">
                            {selectedIncident.documento_fuente_pdf}
                          </div>
                          <div className="pt-1 flex items-center gap-2">
                            <a
                              href={selectedIncident.url_pdf_raw || `/api/documents/raw?filename=${encodeURIComponent(selectedIncident.documento_fuente_pdf)}`}
                              target="_blank"
                              rel="noreferrer"
                              className="px-3 py-1.5 rounded bg-rose-50 hover:bg-rose-100 text-rose-950 text-xs font-semibold border border-rose-300 inline-flex items-center gap-1.5 transition-colors shadow-2xs"
                              title="Abrir PDF original en pestaña nueva"
                            >
                              <IconExternalLink className="w-3.5 h-3.5 text-rose-700" />
                              <span>Abrir PDF Original</span>
                            </a>
                            <button
                              onClick={() => handleInspectDocument(selectedIncident.documento_fuente_pdf)}
                              className="px-3 py-1.5 rounded bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs font-semibold border border-slate-300 inline-flex items-center gap-1.5 transition-colors shadow-2xs"
                              title="Inspeccionar cláusulas extraídas y alertas legales"
                            >
                              <IconSearch className="w-3.5 h-3.5 text-slate-600" />
                              <span>Inspeccionar Cláusula</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Esquema SQL Fuente */}
                      {selectedIncident.esquema_fuente_sql && (
                        <div className="p-3.5 bg-surface-ground rounded border border-surface-border space-y-2">
                          <div className="text-[10px] font-mono text-ink-muted uppercase tracking-wider font-semibold">
                            Esquema de Base de Datos y Tabla Comprometida
                          </div>
                          <div className="font-semibold text-xs text-ink-primary font-mono">
                            Tabla: {selectedIncident.tabla_afectada || 'db_servicios_centrales'}
                          </div>
                          <div className="font-mono text-[11px] text-ink-secondary">
                            Columnas: {Array.isArray(selectedIncident.columnas_afectadas) ? selectedIncident.columnas_afectadas.join(', ') : 'columnas sensibles'}
                          </div>
                          <div className="pt-1 flex items-center gap-2">
                            <a
                              href={selectedIncident.url_sql_raw || `/api/documents/raw?filename=${encodeURIComponent(selectedIncident.esquema_fuente_sql)}`}
                              target="_blank"
                              rel="noreferrer"
                              className="px-3 py-1.5 rounded bg-sky-50 hover:bg-sky-100 text-sky-950 text-xs font-semibold border border-sky-300 inline-flex items-center gap-1.5 transition-colors shadow-2xs font-mono"
                              title="Ver script DDL SQL completo"
                            >
                              <IconExternalLink className="w-3.5 h-3.5 text-sky-700" />
                              <span>Ver DDL SQL Completo</span>
                            </a>
                            <button
                              onClick={() => handleInspectDocument(selectedIncident.esquema_fuente_sql)}
                              className="px-3 py-1.5 rounded bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs font-semibold border border-slate-300 inline-flex items-center gap-1.5 transition-colors shadow-2xs"
                              title="Inspeccionar análisis AST de columnas sensibles"
                            >
                              <IconSearch className="w-3.5 h-3.5 text-slate-600" />
                              <span>Inspeccionar AST</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Texto de la Evidencia o Cláusula Observada */}
                    {selectedIncident.clausula_observada && (
                      <div className="p-3.5 rounded clause-callout space-y-1 shadow-2xs">
                        <div className="text-[10px] font-mono uppercase font-bold" style={{ color: 'var(--clause-bar)' }}>
                          Cláusula / Hallazgo Observado en Peritaje:
                        </div>
                        <div className="font-serif text-xs text-ink-primary italic leading-relaxed">
                          "{selectedIncident.clausula_observada}"
                        </div>
                      </div>
                    )}
                  </div>

                  {/* BLOQUE 2: CALIFICACIÓN JURÍDICA Y EXPOSICIÓN SANCIONADORA ANPD */}
                  <div className="p-5 rounded border border-surface-border bg-surface-card space-y-4">
                    <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
                      <div className="flex items-center gap-2">
                        <IconShield className="w-4 h-4 text-amber-500" />
                        <span className="font-serif font-bold text-sm text-ink-primary">
                          Calificación Jurídica y Exposición Sancionadora ANPD
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-ink-muted">
                        D.S. N° 016-2024-JUS
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div className="p-3.5 rounded kpi-card-multa shadow-2xs">
                        <div className="text-[10px] text-ink-muted font-mono uppercase font-semibold">Multa Máxima Estimada</div>
                        <div className="font-mono text-xl font-bold kpi-num tabular-nums mt-0.5">
                          {selectedIncident.multa_estimada_uit || 12.5} UIT
                        </div>
                        <div className="text-[11px] text-ink-secondary font-mono mt-0.5 font-medium">
                          ~ S/. {((selectedIncident.multa_estimada_uit || 12.5) * 5150).toLocaleString()} PEN
                        </div>
                      </div>

                      <div className="p-3.5 rounded kpi-card-titulares shadow-2xs">
                        <div className="text-[10px] text-ink-muted font-mono uppercase font-semibold">Titulares Comprometidos</div>
                        <div className="font-mono text-xl font-bold kpi-num tabular-nums mt-0.5">
                          {(selectedIncident.num_affected_subjects || 0).toLocaleString()}
                        </div>
                        <div className="text-[11px] text-ink-secondary font-medium">Estudiantes y ciudadanos</div>
                      </div>

                      <div className="p-3.5 rounded kpi-card-anpd shadow-2xs">
                        <div className="text-[10px] text-ink-muted font-mono uppercase font-semibold">Precedente Vinculante ANPD</div>
                        <div className="font-mono text-xs font-bold kpi-num mt-1 line-clamp-1">
                          {selectedIncident.precedente_anpd || "Res. 045-2023-JUS/DGPDP"}
                        </div>
                        <div className="text-[11px] text-ink-muted mt-0.5">Infracción calificada como Grave</div>
                      </div>
                    </div>

                    {/* Nexo Causal y Citas Normativas Interactivas */}
                    <div className="p-3.5 bg-surface-ground rounded border border-surface-border space-y-2">
                      <div className="text-xs text-ink-primary leading-relaxed">
                        <strong>Nexo Causal Técnico-Legal:</strong> Vulneración directa al principio de seguridad y confidencialidad en el tratamiento de datos sensibles. El tratamiento operó sin medidas técnicas ni organizativas proporcionadas al riesgo de los titulares.
                      </div>

                      <div className="pt-2 flex flex-wrap items-center gap-2.5">
                        <button
                          onClick={() => fetchLegalReference('iso27701', selectedIncident.regla?.control_iso27701 || 'A.3.24')}
                          className="px-3 py-1.5 rounded bg-rose-50 hover:bg-rose-100 text-rose-950 text-xs font-mono font-semibold border border-rose-300 transition-colors inline-flex items-center gap-1.5 shadow-2xs"
                        >
                          <span>Ver Norma: ISO/IEC 27701 {selectedIncident.regla?.control_iso27701 || 'A.3.24'}</span>
                          <IconExternalLink className="w-3.5 h-3.5 text-rose-800" />
                        </button>

                        <button
                          onClick={() => fetchLegalReference('ley29733', selectedIncident.regla?.articulo_lpdp || '28')}
                          className="px-3 py-1.5 rounded bg-amber-50 hover:bg-amber-100 text-amber-950 text-xs font-mono font-semibold border border-amber-300 transition-colors inline-flex items-center gap-1.5 shadow-2xs"
                        >
                          <span>Ver Ley 29733: Art. {selectedIncident.regla?.articulo_lpdp || '28'}</span>
                          <IconExternalLink className="w-3.5 h-3.5 text-amber-800" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* BLOQUE 3: PLAN PERICIAL DE REMEDIACIÓN CUADRIDIMENSIONAL (VISIBLE EN EL DOSSIER) */}
                  <div className="p-5 rounded border border-surface-border bg-surface-card space-y-4">
                    <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
                      <div className="flex items-center gap-2">
                        <IconCpu className="w-4 h-4 text-emerald-500" />
                        <span className="font-serif font-bold text-sm text-ink-primary">
                          Plan de Remediación Integral Multidimensional (4 Ejes Mandatorios)
                        </span>
                      </div>
                      <span className="text-[11px] font-mono text-ink-muted">
                        No Reducción a SQL
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Eje 1: Directiva */}
                      <div className="p-4 rounded remediation-axis-1 space-y-2 shadow-2xs">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs font-bold axis-title">Eje I: Directiva Institucional</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded axis-tag font-bold">Organizativa</span>
                        </div>
                        <p className="text-xs text-ink-secondary leading-relaxed">
                          {selectedIncident.remediacion_organizativa || 
                           "Emisión de Resolución Rectoral que reforme la Directiva de Seguridad TI, estableciendo protocolos mandatorios de cifrado en reposo para datos sensibles y roles periciales del CSIRT."}
                        </p>
                      </div>

                      {/* Eje 2: Software / UX */}
                      <div className="p-4 rounded remediation-axis-2 space-y-2 shadow-2xs">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs font-bold axis-title">Eje II: Reingeniería Software & UX</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded axis-tag font-bold">Aplicación</span>
                        </div>
                        <p className="text-xs text-ink-secondary leading-relaxed">
                          {selectedIncident.remediacion_software_nosql || 
                           "Actualización de microservicios y portales web para eliminar casillas pre-marcadas, forzar consentimiento libre y expreso, y deshabilitar almacenamiento local no autorizado."}
                        </p>
                      </div>

                      {/* Eje 3: Contractual / DPA */}
                      <div className="p-4 rounded remediation-axis-3 space-y-2 shadow-2xs">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs font-bold axis-title">Eje III: Blindaje Contractual & DPA</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded axis-tag font-bold">Legal / Proveedor</span>
                        </div>
                        <p className="text-xs text-ink-secondary leading-relaxed">
                          {selectedIncident.remediacion_juridica || 
                           "Suscripción de Acuerdos de Tratamiento de Datos (DPA) con proveedores de nube y pasarelas de pago bajo D.S. 016-2024-JUS, restringiendo transferencias transfronterizas sin autorización."}
                        </p>
                      </div>

                      {/* Eje 4: Técnica / SQL */}
                      <div className="p-4 rounded remediation-axis-4 space-y-2 shadow-2xs">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs font-bold axis-title">Eje IV: Medidas Técnicas en Repositorio</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded axis-tag font-bold">Criptografía DDL</span>
                        </div>
                        <p className="text-xs text-ink-secondary leading-relaxed">
                          {selectedIncident.remediacion_db_sql || 
                           "Aplicación de algoritmo AES-256-GCM para columnas sensibles, migración de contraseñas de MD5 a Argon2id con salt único, y purga periódica de CVV."}
                        </p>
                      </div>
                    </div>
                  </div>

                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-xs text-ink-muted">
                  Seleccione un expediente de la lista para cargar su dossier.
                </div>
              )}
            </main>
          </>
        )}

        {/* ================================================================== */}
        {/* VISTA B: REPOSITORIO DE DOCUMENTOS Y ACTIVOS (TABLA COMPLETA)      */}
        {/* ================================================================== */}
        {activeModule === 'repositorio' && (
          <div className="flex-1 flex flex-col bg-surface-ground p-6 overflow-hidden">
            <div className="max-w-6xl w-full mx-auto flex-1 flex flex-col space-y-4">
              
              {/* Encabezado del Repositorio */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
                <div>
                  <h2 className="font-serif font-bold text-lg text-ink-primary">
                    Repositorio de Instrumentos Documentales y Esquemas DDL
                  </h2>
                  <p className="text-xs text-ink-muted">
                    Inventario central de {documents.length} documentos institucionales auditados bajo ISO/IEC 27701 y Ley 29733.
                  </p>
                </div>

                <div className="relative w-72">
                  <IconSearch className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-ink-muted" />
                  <input
                    type="text"
                    value={searchDoc}
                    onChange={(e) => setSearchDoc(e.target.value)}
                    placeholder="Filtrar instrumentos..."
                    className="w-full bg-surface-card border border-surface-border rounded pl-8 pr-3 py-1.5 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-unsa-700"
                  />
                </div>
              </div>

              {/* Tabla de Documentos */}
              <div className="flex-1 bg-surface-card border border-surface-border rounded overflow-hidden flex flex-col">
                <div className="overflow-x-auto flex-1">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-surface-sidebar border-b border-surface-border font-mono text-ink-muted">
                      <tr>
                        <th className="py-2.5 px-4 font-semibold">Instrumento / Archivo</th>
                        <th className="py-2.5 px-4 font-semibold">Tipo</th>
                        <th className="py-2.5 px-4 font-semibold">Tamaño</th>
                        <th className="py-2.5 px-4 font-semibold">Descripción del Alcance</th>
                        <th className="py-2.5 px-4 font-semibold text-right">Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-border text-ink-primary">
                      {filteredDocs.map((doc, idx) => {
                        const matchLoaded = loadedDocuments.find(ld => ld.nombre_archivo === doc.nombre);
                        const isOriginal = doc.es_original_unsa;

                        return (
                          <tr key={idx} className="hover:bg-surface-elevated transition-colors">
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2.5">
                                <IconFileText className={`w-4 h-4 shrink-0 ${doc.tipo === 'SQL' ? 'text-sky-700' : 'text-rose-700'}`} />
                                <div>
                                  <a
                                    href={doc.raw_url || `/api/documents/raw?filename=${encodeURIComponent(doc.nombre)}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="font-semibold text-slate-900 hover:text-[var(--unsa-primary)] transition-colors inline-flex items-center gap-1.5 leading-snug"
                                    title="Abrir archivo nativo en nueva pestaña"
                                  >
                                    <span>{doc.nombre}</span>
                                    <IconExternalLink className="w-3 h-3 text-slate-500 hover:text-slate-900" />
                                  </a>
                                  {isOriginal && (
                                    <span className="block text-[11px] font-mono text-emerald-800 dark:text-emerald-400 font-bold mt-0.5">
                                      ✓ Documento Oficial UNSA en Custodia
                                    </span>
                                  )}
                                </div>
                              </div>
                            </td>

                            <td className="py-3 px-4 font-mono text-xs">
                              <span className={`px-2 py-0.5 rounded font-bold border ${
                                doc.tipo === 'SQL'
                                  ? 'bg-sky-50 text-sky-900 border-sky-300'
                                  : 'bg-rose-50 text-rose-900 border-rose-300'
                              }`}>
                                {doc.tipo}
                              </span>
                            </td>

                            <td className="py-3 px-4 font-mono text-[11px] text-ink-muted">
                              {(doc.tamano / 1024).toFixed(0)} KB
                            </td>

                            <td className="py-3 px-4 text-ink-secondary max-w-md line-clamp-1">
                              {doc.descripcion}
                            </td>

                            <td className="py-3 px-4 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <button
                                  onClick={() => handleInspectDocument(doc.id || matchLoaded?.id || doc.nombre)}
                                  className="px-2.5 py-1 rounded bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs font-semibold border border-slate-300 inline-flex items-center gap-1.5 transition-colors shadow-2xs"
                                  title="Ver cláusulas y columnas extraídas"
                                >
                                  <IconSearch className="w-3.5 h-3.5 text-slate-700" />
                                  <span>Inspeccionar</span>
                                </button>
                                
                                <a
                                  href={doc.raw_url || `/api/documents/raw?filename=${encodeURIComponent(doc.nombre)}`}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="p-1.5 rounded bg-white hover:bg-rose-50 text-slate-700 hover:text-rose-900 transition-colors border border-slate-300 shadow-2xs"
                                  title="Abrir archivo original en pestaña"
                                >
                                  <IconExternalLink className="w-3.5 h-3.5" />
                                </a>

                                {(doc.id || matchLoaded?.id) && (
                                  <button
                                    onClick={() => handleExcludeDocument(doc.id || matchLoaded.id, doc.nombre)}
                                    className="p-1.5 rounded bg-white hover:bg-rose-50 text-slate-500 hover:text-red-700 transition-colors border border-slate-300 shadow-2xs"
                                    title="Excluir del inventario activo"
                                  >
                                    <IconTrash className="w-3.5 h-3.5" />
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          </div>
        )}

      </div>

      {/* ==================================================================== */}
      {/* 3. DRAWER LATERAL: CONSULTOR DPO & JURISPRUDENCIA ANPD (SLIDE-OVER)  */}
      {/* ==================================================================== */}
      {chatDrawerOpen && (
        <div className="fixed inset-y-0 right-0 w-full sm:w-[440px] bg-surface-card border-l border-surface-border z-40 flex flex-col shadow-2xl">
          
          {/* Cabecera del Drawer */}
          <div className="p-3.5 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
            <div className="flex items-center gap-2">
              <IconCpu className="w-4 h-4 text-[var(--unsa-primary)]" />
              <div>
                <span className="font-serif font-bold text-sm text-ink-primary block">
                  Consultor DPO & Tribunal ANPD
                </span>
                <span className="text-[10px] font-mono text-ink-muted">
                  Grafo ISO 27701 • 588 Casos de Sanción • Protocolo A2A
                </span>
              </div>
            </div>
            
            <button
              onClick={() => setChatDrawerOpen(false)}
              className="p-1 rounded text-ink-muted hover:text-ink-primary transition-colors"
              title="Cerrar panel lateral"
            >
              <IconX className="w-4 h-4" />
            </button>
          </div>

          {/* Contexto del Expediente Activo */}
          {selectedIncident && (
            <div className="p-3 bg-surface-sidebar border-b border-surface-border text-xs font-mono text-ink-primary flex items-center justify-between">
              <span className="truncate">Contexto: <strong className="text-slate-900 font-bold bg-white px-2 py-0.5 rounded border border-slate-300 shadow-2xs">{selectedIncident.incident_code}</strong></span>
              <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-900 border border-amber-300 font-bold text-[11px] shrink-0">{selectedIncident.multa_estimada_uit} UIT máx</span>
            </div>
          )}

          {/* Mensajes del Chat */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start w-full'}`}
              >
                <div className="text-[10px] font-mono text-ink-muted mb-1 px-1 flex items-center gap-1.5">
                  <span>{msg.role === 'user' ? 'Auditor' : 'Oficial de Privacidad (DPO / CSIRT)'}</span>
                  {msg.role === 'assistant' && msg.provenance && (
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-surface-sidebar border border-surface-border text-ink-secondary font-mono">
                      {msg.provenance === 'a2a' ? 'A2A • VPS UNSA' : 'LangGraph • Multi-Agente'}
                    </span>
                  )}
                </div>
                
                <div className={`p-3.5 rounded text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'chat-user-bubble rounded-br-none max-w-[370px]'
                    : 'chat-assistant-bubble rounded-bl-none max-w-[400px] w-full'
                }`}>
                  {msg.role === 'user' ? (
                    <div className="text-white font-sans text-xs whitespace-pre-wrap leading-relaxed select-text font-medium">
                      {msg.content}
                    </div>
                  ) : (
                    <>
                      <div
                        className="legal-markdown text-ink-primary"
                        dangerouslySetInnerHTML={renderLegalMarkdown(msg.content)}
                      />

                      {/* BOTÓN DISCRETO: FLUJO DE AGENTES Y TRAZABILIDAD MULTI-AGENTE */}
                      {msg.trazabilidad && msg.trazabilidad.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-surface-border">
                          <button
                            type="button"
                            onClick={() => toggleFlowMessage(i)}
                            className="w-full flex items-center justify-between text-[11px] font-mono px-2.5 py-1.5 rounded bg-surface-ground hover:bg-surface-elevated text-ink-secondary hover:text-ink-primary border border-surface-border transition-colors cursor-pointer select-none"
                            title="Inspeccionar la tubería multi-agente y nodos que intervinieron"
                          >
                            <span className="inline-flex items-center gap-1.5">
                              <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
                              <strong className="text-ink-primary">Flujo de Agentes ({msg.trazabilidad.length} nodos)</strong>
                            </span>
                            <span className="text-[10px] text-ink-muted font-medium">
                              {expandedFlows[i] ? '▲ Ocultar' : '▼ Ver Nodos'}
                            </span>
                          </button>

                          {expandedFlows[i] && (
                            <div className="mt-2 p-2.5 rounded bg-surface-ground border border-surface-border space-y-1.5 text-[11px] font-mono">
                              <div className="text-[10px] uppercase font-bold text-ink-muted tracking-wider pb-1 border-b border-surface-border flex items-center justify-between">
                                <span>Orquestación Pericial:</span>
                                <span className="text-emerald-700 font-bold">100% Auditado</span>
                              </div>
                              <div className="space-y-1 pt-0.5">
                                {msg.trazabilidad.map((t, tidx) => (
                                  <div key={tidx} className="flex items-start gap-1.5 py-0.5 border-b border-surface-border/50 last:border-b-0">
                                    <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold shrink-0 mt-0.5 font-mono ${
                                      t.estado === 'ok' ? 'bg-emerald-100 text-emerald-900 border border-emerald-300' :
                                      t.estado === 'warn' ? 'bg-amber-100 text-amber-900 border border-amber-300' :
                                      'bg-sky-100 text-sky-900 border border-sky-300'
                                    }`}>
                                      {t.agente || `Nodo ${tidx+1}`}
                                    </span>
                                    <span className="text-[10px] text-ink-secondary leading-tight">
                                      {t.accion || t.detalle || 'Ejecución pericial completada'}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}

            {/* ESTADO DE CARGA REAL CON FEEDBACK MULTI-AGENTE */}
            {chatLoading && (
              <div className="flex flex-col items-start w-full">
                <div className="text-[10px] font-mono text-ink-muted mb-1 px-1">
                  Oficial de Privacidad (DPO / CSIRT)
                </div>
                <div className="p-3.5 rounded bg-surface-card border border-surface-border max-w-[390px] w-full rounded-bl-none shadow-sm space-y-2">
                  <div className="flex items-center gap-2 text-xs font-serif font-bold text-ink-primary">
                    <div className="w-4 h-4 border-2 border-[var(--unsa-primary)] border-t-transparent rounded-full animate-spin shrink-0"></div>
                    <span>Procesando consulta en Grafo Multi-Agente...</span>
                  </div>
                  <div className="text-[10px] font-mono text-ink-muted leading-relaxed pl-6">
                    Supervisor ➔ DSPM Risk ➔ Precedentes ANPD ➔ GPT-6 Luna ➔ Reflection
                  </div>
                </div>
              </div>
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Preguntas Sugeridas */}
          <div className="p-2.5 border-t border-surface-border bg-surface-ground flex flex-wrap gap-2">
            {[
              "¿Cuál es el nexo causal con la Ley 29733?",
              "¿Qué sanción aplica la ANPD según D.S. 016-2024?",
              "¿Qué adenda DPA se exige a Google Workspace?"
            ].map((sug, idx) => (
              <button
                key={idx}
                onClick={() => handleSendChat(sug)}
                disabled={chatLoading}
                className="px-2.5 py-1 rounded bg-white hover:bg-rose-50 text-slate-800 hover:text-rose-900 border border-slate-300 text-xs font-medium transition-colors shadow-2xs disabled:opacity-50"
              >
                {sug}
              </button>
            ))}
          </div>

          {/* Input de Consulta */}
          <div className="p-3 border-t border-surface-border bg-surface-sidebar flex items-center gap-2">
            <input
              type="text"
              value={chatInput}
              disabled={chatLoading}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !chatLoading && handleSendChat()}
              placeholder={chatLoading ? "El orquestador multi-agente está procesando..." : "Preguntar al DPO o consultar sanciones..."}
              className="flex-1 bg-white border border-surface-border rounded px-3 py-1.5 text-xs text-ink-primary placeholder-ink-muted focus:outline-none focus:border-unsa-700 shadow-2xs disabled:bg-slate-100 disabled:opacity-75"
            />
            <button
              onClick={() => handleSendChat()}
              disabled={chatLoading || !chatInput.trim()}
              className="px-3.5 py-1.5 rounded bg-[var(--unsa-primary)] hover:bg-[var(--unsa-hover)] disabled:opacity-50 text-white text-xs font-semibold transition-colors inline-flex items-center gap-1.5 shadow-2xs cursor-pointer disabled:cursor-not-allowed"
            >
              {chatLoading ? (
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <IconSend className="w-3.5 h-3.5" />
              )}
            </button>
          </div>

        </div>
      )}

      {/* ==================================================================== */}
      {/* 4. MODALES: INSPECCIÓN DOCUMENTAL, CITAS LEGALES Y CONFIRMACIÓN      */}
      {/* ==================================================================== */}

      {/* MODAL DE INSPECCIÓN DE DOCUMENTO */}
      {inspectDocModal.open && (
        <div className="fixed inset-0 backdrop-blur-xs z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'var(--modal-overlay)' }}>
          <div className="bg-surface-card border border-surface-border rounded max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            
            <div className="p-4 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
              <div>
                <h3 className="font-serif font-bold text-sm text-ink-primary">
                  Inspección de Instrumento: {inspectDocModal.data?.archivo?.nombre_archivo}
                </h3>
                <span className="text-[11px] font-mono text-ink-secondary">
                  ID: {inspectDocModal.data?.archivo?.id} • Tipo: {inspectDocModal.data?.archivo?.tipo_archivo}
                </span>
              </div>
              <button
                onClick={() => setInspectDocModal({ open: false, loading: false, data: null })}
                className="text-ink-muted hover:text-ink-primary"
              >
                <IconX className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex-1 overflow-y-auto space-y-4 text-xs">
              {inspectDocModal.loading ? (
                <div className="p-8 text-center text-ink-muted font-mono">
                  Cargando análisis de cláusulas y columnas AST...
                </div>
              ) : (
                <>
                  <div className="p-3 bg-surface-ground rounded border border-surface-border font-mono text-[11px] space-y-1">
                    <div>Resumen: {inspectDocModal.data?.archivo?.resumen_analisis}</div>
                    <div>Fecha de Ingesta: {inspectDocModal.data?.archivo?.fecha_carga}</div>
                    {inspectDocModal.data?.raw_url && (
                      <div className="pt-2">
                        <a
                          href={inspectDocModal.data.raw_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-950 font-semibold rounded border border-rose-300 font-sans text-xs transition-colors shadow-2xs"
                        >
                          <IconExternalLink className="w-3.5 h-3.5 text-rose-700" />
                          <span>Abrir Instrumento Nativo (PDF/SQL)</span>
                        </a>
                      </div>
                    )}
                  </div>

                  {/* Cláusulas extraídas */}
                  {inspectDocModal.data?.clausulas?.length > 0 && (
                    <div className="space-y-2">
                      <div className="font-serif font-bold text-sm text-ink-primary">
                        Cláusulas y Artículos Normativos ({inspectDocModal.data.clausulas.length})
                      </div>
                      <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                        {inspectDocModal.data.clausulas.map((c, i) => (
                          <div key={i} className="p-3 bg-surface-ground rounded border border-surface-border text-[11px] space-y-1">
                            <div className="flex items-center justify-between font-mono">
                              <span className="font-bold text-ink-primary">{c.numero_clausula || `Artículo ${i+1}`}</span>
                              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                                c.estado_cumplimiento === 'OBSERVADO'
                                  ? 'bg-rose-50 text-rose-900 border border-rose-300'
                                  : 'bg-emerald-50 text-emerald-900 border border-emerald-300'
                              }`}>
                                {c.estado_cumplimiento}
                              </span>
                            </div>
                            <p className="text-ink-secondary">{c.texto_clausula}</p>
                            {c.alerta_legal && (
                              <div className="text-amber-800 font-bold text-[10px] font-mono">
                                Alerta Legal: {c.alerta_legal}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Columnas si es esquema SQL */}
                  {inspectDocModal.data?.columnas_sensibles?.length > 0 && (
                    <div className="space-y-2">
                      <div className="font-serif font-bold text-sm text-ink-primary">
                        Columnas Sensibles Identificadas por AST ({inspectDocModal.data.columnas_sensibles.length})
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-60 overflow-y-auto">
                        {inspectDocModal.data.columnas_sensibles.map((col, i) => (
                          <div key={i} className="p-2.5 bg-surface-ground rounded border border-surface-border text-[11px] font-mono space-y-1">
                            <div className="font-bold text-ink-primary">{col.nombre_tabla}.{col.nombre_columna}</div>
                            <div className="text-rose-500 font-medium">{col.categoria_sensible}</div>
                            <div className="text-ink-muted text-[10px]">{col.recomendacion_seguridad}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="p-3 border-t border-surface-border bg-surface-sidebar flex justify-end">
              <button
                onClick={() => setInspectDocModal({ open: false, loading: false, data: null })}
                className="px-4 py-1.5 rounded bg-surface-card hover:bg-surface-elevated text-ink-primary text-xs font-medium border border-surface-border"
              >
                Cerrar
              </button>
            </div>

          </div>
        </div>
      )}

      {/* MODAL DE REFERENCIA LEGAL Y NORMATIVA (REPARADO Y CONECTADO) */}
      {legalModal.open && (
        <div className="fixed inset-0 backdrop-blur-xs z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'var(--modal-overlay)' }}>
          <div className="bg-surface-card border border-surface-border rounded max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl overflow-hidden">
            
            <div className="p-4 border-b border-surface-border bg-surface-sidebar flex items-center justify-between">
              <div>
                <h3 className="font-serif font-bold text-sm text-ink-primary">
                  {legalModal.tipo === 'iso27701' || legalModal.tipo === 'control' ? 'Control ISO/IEC 27701:2025' : 'Artículo de la Ley N° 29733 (ANPD)'}
                </h3>
                <span className="text-xs font-mono font-bold text-rose-900 dark:text-rose-300">
                  {legalModal.data?.control_id ? `Control: ${legalModal.data.control_id}` : legalModal.data?.articulo ? `Artículo: ${legalModal.data.articulo}` : 'Referencia Normativa Oficial'}
                </span>
              </div>
              <button
                onClick={() => setLegalModal({ open: false, loading: false, tipo: '', data: null })}
                className="text-ink-muted hover:text-ink-primary"
              >
                <IconX className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 flex-1 overflow-y-auto space-y-3 text-xs leading-relaxed text-ink-primary">
              {legalModal.loading ? (
                <div className="p-8 text-center text-ink-muted font-mono">Consultando repositorio normativo...</div>
              ) : (
                <>
                  <div className="font-serif font-bold text-sm text-ink-primary">
                    {legalModal.data?.titulo || legalModal.data?.nombre || 'Norma Oficial'}
                  </div>
                  
                  <div className="p-3.5 bg-surface-ground rounded border border-surface-border font-serif text-ink-secondary italic leading-relaxed whitespace-pre-line">
                    "{legalModal.data?.texto_oficial || legalModal.data?.descripcion}"
                  </div>

                  {legalModal.data?.guia_implementacion && (
                    <div className="p-3.5 bg-amber-50 rounded border border-amber-300 space-y-1">
                      <div className="font-mono text-xs text-amber-900 uppercase font-bold tracking-wide">Exigibilidad y Supervisión ANPD:</div>
                      <p className="text-amber-950 font-sans text-xs leading-relaxed">{legalModal.data.guia_implementacion}</p>
                    </div>
                  )}

                  {legalModal.data?.principios_vinculados?.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <div className="font-mono text-[10px] text-ink-muted uppercase font-semibold">Principios ISO/IEC 29100 Vinculados:</div>
                      <div className="flex flex-wrap gap-1.5">
                        {legalModal.data.principios_vinculados.map((p, i) => (
                          <span key={i} className="px-2.5 py-0.5 rounded bg-sky-50 border border-sky-300 text-xs font-mono font-semibold text-sky-900">
                            {p.name || p.id}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="p-3 border-t border-surface-border bg-surface-sidebar flex justify-end">
              <button
                onClick={() => setLegalModal({ open: false, loading: false, tipo: '', data: null })}
                className="px-4 py-1.5 rounded bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs font-semibold border border-slate-300 shadow-2xs"
              >
                Entendido
              </button>
            </div>

          </div>
        </div>
      )}

      {/* MODAL DE CONFIRMACIÓN */}
      {confirmModal.open && (
        <div className="fixed inset-0 backdrop-blur-xs z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'var(--modal-overlay)' }}>
          <div className="bg-surface-card border border-surface-border rounded max-w-md w-full p-5 space-y-4 shadow-2xl">
            <div className="font-serif font-bold text-sm text-ink-primary">
              {confirmModal.title}
            </div>
            <p className="text-xs text-ink-secondary leading-relaxed">
              {confirmModal.message}
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setConfirmModal({ open: false, title: '', message: '', onConfirm: null })}
                className="px-3 py-1.5 rounded bg-surface-card hover:bg-surface-elevated text-ink-secondary text-xs font-medium border border-surface-border"
              >
                Cancelar
              </button>
              <button
                onClick={confirmModal.onConfirm}
                className={`px-3 py-1.5 rounded text-white text-xs font-medium ${
                  confirmModal.danger
                    ? 'bg-rose-700 hover:bg-rose-600'
                    : 'bg-unsa-800 hover:bg-unsa-700'
                }`}
              >
                Confirmar Acción
              </button>
            </div>
          </div>
        </div>
      )}

      {/* NOTIFICACIÓN TOAST */}
      {toast.visible && (
        <div className="fixed bottom-4 left-4 z-50 px-4 py-2.5 rounded bg-surface-card border border-surface-borderLight text-xs text-ink-primary shadow-xl flex items-center gap-2 font-mono">
          <span className={`w-2.5 h-2.5 rounded-full ${toast.type === 'error' ? 'bg-rose-500' : toast.type === 'success' ? 'bg-emerald-500' : 'bg-[var(--unsa-primary)]'}`}></span>
          <span>{toast.message}</span>
        </div>
      )}

    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
