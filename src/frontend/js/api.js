// ==============================================================================
// API Helpers, Constantes ISO/IEC 27701:2025 y Renderizador Markdown Legal
// ==============================================================================

(function () {
  if (window.marked) {
    window.marked.setOptions({ gfm: true, breaks: true });
  }

  function getActorId() {
    const saved = localStorage.getItem('pims_a6_actor_id');
    return saved ? parseInt(saved, 10) : 601;
  }

  function setActorId(id) {
    localStorage.setItem('pims_a6_actor_id', String(id));
  }

  async function apiFetch(url, options = {}) {
    const headers = Object.assign({}, options.headers || {}, {
      'X-Actor-Id': String(getActorId()),
    });
    if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }
    return fetch(url, Object.assign({}, options, { headers }));
  }

  const STATUS_MAP = {
    I: { label: 'En Investigación', short: 'I', cls: 'bg-amber-50 text-amber-900 border-amber-300' },
    E: { label: 'En Mitigación', short: 'E', cls: 'bg-sky-50 text-sky-900 border-sky-300' },
    C: { label: 'Cerrado', short: 'C', cls: 'bg-emerald-50 text-emerald-900 border-emerald-300' },
  };

  const SEVERITY_MAP = {
    C: { label: 'Crítico', cls: 'bg-rose-100 text-rose-900 border-rose-300' },
    A: { label: 'Alto', cls: 'bg-orange-100 text-orange-900 border-orange-300' },
    M: { label: 'Medio', cls: 'bg-amber-50 text-amber-900 border-amber-300' },
    B: { label: 'Bajo', cls: 'bg-slate-100 text-slate-700 border-slate-300' },
  };

  const TYPE_MAP = {
    BF: { label: 'Brecha Confidencialidad (BF)', cls: 'bg-rose-50 text-rose-900 border-rose-200' },
    BI: { label: 'Brecha Integridad (BI)', cls: 'bg-orange-50 text-orange-900 border-orange-200' },
    BD: { label: 'Brecha Disponibilidad (BD)', cls: 'bg-amber-50 text-amber-900 border-amber-200' },
    PI: { label: 'No Conformidad Principios (PI)', cls: 'bg-purple-50 text-purple-900 border-purple-200' },
    IT: { label: 'Incidente Técnico sin PII (IT)', cls: 'bg-slate-100 text-slate-800 border-slate-300' },
  };

  const MC_STATUS_MAP = {
    ABIERTA: { label: 'Abierta', cls: 'bg-rose-50 text-rose-900 border-rose-300' },
    EN_PROGRESO: { label: 'En Progreso', cls: 'bg-amber-50 text-amber-900 border-amber-300' },
    IMPLEMENTADA: { label: 'Implementada', cls: 'bg-sky-50 text-sky-900 border-sky-300' },
    VERIFICADA: { label: 'Verificada', cls: 'bg-emerald-50 text-emerald-900 border-emerald-300' },
    NO_REQUIERE: { label: 'No Requiere', cls: 'bg-slate-100 text-slate-700 border-slate-300' },
  };

  function renderLegalMarkdown(text) {
    if (!text) return { __html: '' };
    const clean = String(text)
      .replace(/<button[^>]*>.*?<\/button>/gi, '')
      .replace(/[\u{1F4DC}\u{2696}]/gu, '');

    let processed = clean
      .replace(/\[(?:Ref:\s*)?ISO\s*27701\s*([0-9a-zA-Z.]+)\]/gi, '@@@TOKEN_ISO_$1@@@')
      .replace(/\[(?:Ref:\s*)?Ley\s*29733\s*Art\.?\s*([0-9\w-]+)\]/gi, '@@@TOKEN_LEY_$1@@@')
      .replace(/\bISO(?:\/IEC)?\s*27701(?::2025)?\s+(?:[Cc]ontrol\s+)?([A-Za-z]\.[0-9]+(?:\.[0-9]+)?)\b/g, '@@@TOKEN_ISO_$1@@@')
      .replace(/\bLey\s*(?:N\.?\s*°?\s*)?29733(?:\s*,\s*|\s+)Art(?:ículo|\.)?\s*([0-9\w-]+)\b/gi, '@@@TOKEN_LEY_$1@@@');

    processed = processed
      .replace(/@@@TOKEN_ISO_([0-9a-zA-Z.]+)@@@/g, (_, p) =>
        `<button type="button" onclick="window.fetchLegalRefGlobal && window.fetchLegalRefGlobal('iso27701', '${p}')" class="inline-flex items-center px-1.5 py-0.5 rounded bg-rose-50 hover:bg-rose-100 text-rose-900 border border-rose-300 text-[11px] font-mono font-semibold cursor-pointer mx-0.5">ISO 27701 ${p}</button>`
      )
      .replace(/@@@TOKEN_LEY_([0-9\w-]+)@@@/g, (_, p) =>
        `<button type="button" onclick="window.fetchLegalRefGlobal && window.fetchLegalRefGlobal('ley29733', '${p}')" class="inline-flex items-center px-1.5 py-0.5 rounded bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 text-[11px] font-mono font-semibold cursor-pointer mx-0.5">Ley 29733 Art. ${p}</button>`
      );

    return { __html: window.marked ? window.marked.parse(processed) : processed };
  }

  window.PIMS_API = {
    getActorId,
    setActorId,
    apiFetch,
    STATUS_MAP,
    SEVERITY_MAP,
    TYPE_MAP,
    MC_STATUS_MAP,
    renderLegalMarkdown,
  };
})();
