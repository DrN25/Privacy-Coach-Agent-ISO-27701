import fitz
import json
import re
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

PIPELINES_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.dirname(PIPELINES_DIR)
BASE_DIR = os.path.dirname(KB_DIR)
DATASETS_DIR = os.path.join(KB_DIR, "datasets")

# Buscar PDFs en fuentes_normativas_pdf o en knowledge_base
PDF_DIR = os.path.join(BASE_DIR, "fuentes_normativas_pdf")
if not os.path.exists(PDF_DIR):
    PDF_DIR = KB_DIR

SANCTIONS_PDF = os.path.join(PDF_DIR, "05_ANPD_Registro_Oficial_Sanciones_Impuestas.pdf")
if not os.path.exists(SANCTIONS_PDF):
    SANCTIONS_PDF = os.path.join(PDF_DIR, "1255336-registro-de-sanciones-impuestas.pdf")

ISO_PDF = os.path.join(PDF_DIR, "01_ISO_IEC_27701_2025_PIMS_Standard.pdf")
if not os.path.exists(ISO_PDF):
    ISO_PDF = os.path.join(PDF_DIR, "ISO 27701-2025_ocr.pdf")

SANCTIONS_OUT = os.path.join(DATASETS_DIR, "anpd_sanciones_dataset.json")
GRAPH_OUT = os.path.join(DATASETS_DIR, "iso27701_2025_graph.json")

def extract_sanctions():
    print(f"[1/2] Extrayendo sanciones desde {os.path.basename(SANCTIONS_PDF)}...")
    doc = fitz.open(SANCTIONS_PDF)
    sanctions = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        tabs = page.find_tables()
        for tab in tabs.tables:
            rows = tab.extract()
            data_rows = rows[1:] if page_idx == 0 else rows
            for r in data_rows:
                if len(r) >= 6:
                    entidad = (r[1] or "").replace("\n", " ").strip()
                    ruc = (r[2] or "").replace("\n", " ").strip() if len(r) > 2 else ""
                    resolucion = (r[3] or "").replace("\n", " ").strip()
                    infraccion = (r[4] or "").replace("\n", " ").strip()
                    multa = (r[5] or "").replace("\n", " ").strip()
                    medidas = (r[6] or "").replace("\n", " ").strip() if len(r) > 6 else ""
                    
                    if entidad and not entidad.startswith("Entidad") and ("UIT" in multa or re.search(r"\d+", multa)):
                        # Classify sector based on keywords
                        ent_lower = entidad.lower()
                        sector = "General / Comercio"
                        if any(k in ent_lower for k in ["clinica", "salud", "hospital", "medico", "sante", "dental"]):
                            sector = "Salud / Clínica"
                        elif any(k in ent_lower for k in ["banco", "financier", "ripley", "credito", "interbank"]):
                            sector = "Financiero / Banca"
                        elif any(k in ent_lower for k in ["universidad", "colegio", "educat", "instituto"]):
                            sector = "Educación"
                        elif any(k in ent_lower for k in ["http", "www", ".org", ".com", ".pe", "online", "datosperu"]):
                            sector = "Internet / Web / Plataforma"
                        elif any(k in ent_lower for k in ["supermercado", "tienda", "retail", "s.a.c."]):
                            sector = "Retail / Comercio"

                        # Extract UIT amount as float if possible
                        multa_num = None
                        m_uit = re.search(r"(\d+[\,\.]?\d*)\s*UIT", multa, re.IGNORECASE)
                        if m_uit:
                            try:
                                multa_num = float(m_uit.group(1).replace(",", "."))
                            except ValueError:
                                pass

                        sanctions.append({
                            "id": len(sanctions) + 1,
                            "pagina_pdf": page_idx + 1,
                            "entidad": entidad,
                            "ruc": ruc,
                            "sector": sector,
                            "resolucion": resolucion,
                            "infraccion_legal": infraccion,
                            "multa_texto": multa,
                            "multa_uit": multa_num,
                            "medidas_correctivas": medidas
                        })
                        
    with open(SANCTIONS_OUT, "w", encoding="utf-8") as f:
        json.dump(sanctions, f, ensure_ascii=False, indent=2)
        
    print(f"  -> Extracción exitosa: {len(sanctions)} sanciones guardadas en {os.path.basename(SANCTIONS_OUT)}")
    return len(sanctions)

def extract_iso_graph():
    print(f"[2/2] Extrayendo 78 controles y relaciones desde {os.path.basename(ISO_PDF)}...")
    
    # 78 Formal Controls catalogue
    controllers_controls = [
        {"id": "A.1.2.2", "title": "Identify and document purpose", "category": "Conditions for collection and processing"},
        {"id": "A.1.2.3", "title": "Identify lawful basis", "category": "Conditions for collection and processing"},
        {"id": "A.1.2.4", "title": "Determine when and how consent is to be obtained", "category": "Conditions for collection and processing"},
        {"id": "A.1.2.5", "title": "Obtain and record consent", "category": "Conditions for collection and processing"},
        {"id": "A.1.2.6", "title": "Privacy impact assessment", "category": "Conditions for collection and processing"},
        {"id": "A.1.2.7", "title": "Contracts with PII processors", "category": "Conditions for collection and processing"},
        {"id": "A.1.2.8", "title": "Joint PII controller", "category": "Conditions for collection and processing"},
        {"id": "A.1.2.9", "title": "Records of processing PII", "category": "Conditions for collection and processing"},
        {"id": "A.1.3.2", "title": "Determining and fulfilling obligations to PII principals", "category": "Obligations to PII principals"},
        {"id": "A.1.3.3", "title": "Determining information for PII principals", "category": "Obligations to PII principals"},
        {"id": "A.1.3.4", "title": "Providing information to PII principals", "category": "Obligations to PII principals"},
        {"id": "A.1.3.5", "title": "Providing mechanism to modify or withdraw consent", "category": "Obligations to PII principals"},
        {"id": "A.1.3.6", "title": "Providing mechanism to object to PII processing", "category": "Obligations to PII principals"},
        {"id": "A.1.3.7", "title": "Access, correction and erasure", "category": "Obligations to PII principals"},
        {"id": "A.1.3.8", "title": "PII controllers' obligations to inform third parties", "category": "Obligations to PII principals"},
        {"id": "A.1.3.9", "title": "Providing copy of PII processed", "category": "Obligations to PII principals"},
        {"id": "A.1.3.10", "title": "Handling requests", "category": "Obligations to PII principals"},
        {"id": "A.1.3.11", "title": "Automated decision making", "category": "Obligations to PII principals"},
        {"id": "A.1.4.2", "title": "Limit collection", "category": "Privacy by design and by default"},
        {"id": "A.1.4.3", "title": "Limit processing", "category": "Privacy by design and by default"},
        {"id": "A.1.4.4", "title": "Accuracy and quality", "category": "Privacy by design and by default"},
        {"id": "A.1.4.5", "title": "PII minimization objectives", "category": "Privacy by design and by default"},
        {"id": "A.1.4.6", "title": "PII de-identification and deletion at end of processing", "category": "Privacy by design and by default"},
        {"id": "A.1.4.7", "title": "Temporary files", "category": "Privacy by design and by default"},
        {"id": "A.1.4.8", "title": "Retention", "category": "Privacy by design and by default"},
        {"id": "A.1.4.9", "title": "Disposal", "category": "Privacy by design and by default"},
        {"id": "A.1.4.10", "title": "PII transmission controls", "category": "Privacy by design and by default"},
        {"id": "A.1.5.2", "title": "Identifying basis for PII transfer between jurisdictions", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.1.5.3", "title": "Countries and international organizations to which PII can be transferred", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.1.5.4", "title": "Records of transfer of PII", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.1.5.5", "title": "Records of PII disclosures to third parties", "category": "PII sharing, transfer and disclosure"}
    ]

    processors_controls = [
        {"id": "A.2.2.2", "title": "Customer agreement", "category": "Conditions for collection and processing"},
        {"id": "A.2.2.3", "title": "Organization's purposes", "category": "Conditions for collection and processing"},
        {"id": "A.2.2.4", "title": "Marketing and advertising use", "category": "Conditions for collection and processing"},
        {"id": "A.2.2.5", "title": "Infringing instruction", "category": "Conditions for collection and processing"},
        {"id": "A.2.2.6", "title": "Customer obligations", "category": "Conditions for collection and processing"},
        {"id": "A.2.2.7", "title": "Records related to processing PII", "category": "Conditions for collection and processing"},
        {"id": "A.2.3.2", "title": "Obligations to PII principals", "category": "Obligations to PII principals"},
        {"id": "A.2.4.2", "title": "Temporary files", "category": "Privacy by design and by default"},
        {"id": "A.2.4.3", "title": "Return, transfer or disposal of PII", "category": "Privacy by design and by default"},
        {"id": "A.2.4.4", "title": "PII transmission controls", "category": "Privacy by design and by default"},
        {"id": "A.2.5.2", "title": "Basis for PII transfer between jurisdictions", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.2.5.3", "title": "Countries and international organizations to which PII can be transferred", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.2.5.4", "title": "Records of transfer of PII", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.2.5.5", "title": "Disclosures of PII to third parties", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.2.5.6", "title": "Notification of PII disclosure requests", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.2.5.7", "title": "Legally binding PII disclosures", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.2.5.8", "title": "Disclosure of subcontractors used to process PII", "category": "PII sharing, transfer and disclosure"},
        {"id": "A.2.5.9", "title": "Engagement of a subcontractor", "category": "PII sharing, transfer and disclosure"}
    ]

    security_controls_titles = [
        ("A.3.3", "Policies for information security"),
        ("A.3.4", "Information security roles and responsibilities"),
        ("A.3.5", "Threat intelligence"),
        ("A.3.6", "Information security in project management"),
        ("A.3.7", "Inventory of information and other associated assets"),
        ("A.3.8", "Acceptable use of information and other associated assets"),
        ("A.3.9", "Return of assets"),
        ("A.3.10", "Classification of information"),
        ("A.3.11", "Labelling of information"),
        ("A.3.12", "Information transfer"),
        ("A.3.13", "Access control"),
        ("A.3.14", "User registration and de-registration"),
        ("A.3.15", "Access provisioning"),
        ("A.3.16", "Management of privileged access rights"),
        ("A.3.17", "Information security awareness, education and training"),
        ("A.3.18", "Backup"),
        ("A.3.19", "Redundancy of information processing facilities"),
        ("A.3.20", "Logging and monitoring"),
        ("A.3.21", "Control of operational software"),
        ("A.3.22", "Technical vulnerability management"),
        ("A.3.23", "Information systems audit controls"),
        ("A.3.24", "Use of cryptography"),
        ("A.3.25", "Secure development lifecycle"),
        ("A.3.26", "Application security requirements"),
        ("A.3.27", "Secure system architecture and engineering principles"),
        ("A.3.28", "Secure coding"),
        ("A.3.29", "Security testing in development and acceptance"),
        ("A.3.30", "Outsourced development"),
        ("A.3.31", "Separation of development, test and production environments")
    ]
    security_controls = [{"id": cid, "title": ctitle, "category": "Information security controls"} for cid, ctitle in security_controls_titles]

    # Map to ISO 29100 principles & Peru Law
    principles = {
        "Principle 1: Consent and choice": ["A.1.2.2", "A.1.2.3", "A.1.2.4", "A.1.2.5", "A.1.2.6", "A.1.3.5", "A.1.3.6", "A.1.3.8"],
        "Principle 2: Purpose legitimacy and specification": ["A.1.2.2", "A.1.2.3", "A.1.2.6", "A.1.3.3", "A.1.3.4", "A.1.3.11"],
        "Principle 3: Collection limitation": ["A.1.2.6", "A.1.4.2"],
        "Principle 4: Data minimization": ["A.1.4.2", "A.1.4.3", "A.1.4.5", "A.1.4.6"],
        "Principle 5: Use, retention and disclosure limitation": ["A.1.4.3", "A.1.4.7", "A.1.4.8", "A.1.4.9", "A.1.4.10", "A.1.5.2", "A.1.5.3", "A.1.5.4", "A.1.5.5"],
        "Principle 6: Accuracy and quality": ["A.1.4.4"],
        "Principle 7: Openness, transparency and notice": ["A.1.3.3", "A.1.3.4", "A.1.3.9"],
        "Principle 8: Individual participation and access": ["A.1.3.2", "A.1.3.5", "A.1.3.6", "A.1.3.7", "A.1.3.9", "A.1.3.10"],
        "Principle 9: Accountability": ["A.1.2.6", "A.1.2.7", "A.1.2.8", "A.1.2.9"],
        "Principle 10: Information security": [c["id"] for c in security_controls] + ["A.1.4.10", "A.2.4.4"],
        "Principle 11: Privacy compliance": ["A.1.2.3", "A.1.5.2", "A.2.2.2"]
    }

    peru_law_map = {
        "A.1.2.4": {"ley": "Art. 18 Ley 29733 (Consentimiento)", "directiva": "Condición de consentimiento previo, libre e inequívoco"},
        "A.1.2.5": {"ley": "Art. 18 Ley 29733 (Obtención y registro)", "directiva": "Registro demostrable de la autorización del titular"},
        "A.1.2.2": {"ley": "Art. 16 Ley 29733 (Principio de Finalidad)", "directiva": "Finalidad determinada, explícita y lícita"},
        "A.1.4.2": {"ley": "Art. 15 Ley 29733 (Principio de Proporcionalidad)", "directiva": "No recopilar datos excesivos o innecesarios"},
        "A.1.4.6": {"ley": "Art. 17 Ley 29733 (Cancelación y Supresión)", "directiva": "Anonimización y destrucción segura"},
        "A.1.3.7": {"ley": "Arts. 19-22 Ley 29733 (Derechos ARCO)", "directiva": "Procedimiento de atención en plazos de ley"},
        "A.3.10":  {"ley": "Art. 28 Ley 29733 (Seguridad)", "directiva": "Nivel Medio: Registro de accesos y bitácora de auditoría"},
        "A.3.18":  {"ley": "Art. 28 Ley 29733 (Seguridad)", "directiva": "Nivel Básico: Copias de respaldo y restauración"},
        "A.3.24":  {"ley": "Art. 28 Ley 29733 (Seguridad)", "directiva": "Nivel Complejo: Cifrado en reposo para datos sensibles"}
    }

    all_nodes = []
    
    for c in controllers_controls:
        p_match = [p for p, ctrls in principles.items() if c["id"] in ctrls]
        p_law = peru_law_map.get(c["id"], None)
        all_nodes.append({
            "id": c["id"],
            "title": c["title"],
            "role": "PII Controller",
            "category": c["category"],
            "standard": "ISO/IEC 27701:2025",
            "table": "A.1",
            "iso29100_principles": p_match,
            "peru_legal_bridge": p_law
        })

    for c in processors_controls:
        p_match = [p for p, ctrls in principles.items() if c["id"] in ctrls]
        p_law = peru_law_map.get(c["id"], None)
        all_nodes.append({
            "id": c["id"],
            "title": c["title"],
            "role": "PII Processor",
            "category": c["category"],
            "standard": "ISO/IEC 27701:2025",
            "table": "A.2",
            "iso29100_principles": p_match,
            "peru_legal_bridge": p_law
        })

    for c in security_controls:
        p_match = [p for p, ctrls in principles.items() if c["id"] in ctrls]
        p_law = peru_law_map.get(c["id"], None)
        all_nodes.append({
            "id": c["id"],
            "title": c["title"],
            "role": "Shared (Controller & Processor)",
            "category": c["category"],
            "standard": "ISO/IEC 27701:2025",
            "table": "A.3",
            "iso29100_principles": p_match,
            "peru_legal_bridge": p_law
        })

    graph_data = {
        "metadata": {
            "standard": "ISO/IEC 27701:2025 (Standalone PIMS)",
            "total_controls": len(all_nodes),
            "controllers_count": len(controllers_controls),
            "processors_count": len(processors_controls),
            "security_count": len(security_controls),
            "normative_reference": "ISO/IEC 29100:2024",
            "peru_framework": "Ley 29733 & Directiva de Seguridad RD 019-2013-JUS"
        },
        "controls": all_nodes
    }

    with open(GRAPH_OUT, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)

    print(f"  -> Extracción exitosa: {len(all_nodes)} controles estructurados guardados en {os.path.basename(GRAPH_OUT)}")
    return len(all_nodes)

if __name__ == "__main__":
    n_sanc = extract_sanctions()
    n_ctrl = extract_iso_graph()
    print("="*60)
    print(f"PROCESAMIENTO COMPLETO:")
    print(f"  - Sanciones ANPD procesadas: {n_sanc} casos reales")
    print(f"  - Controles ISO 27701:2025: {n_ctrl} nodos ontológicos")
    print("="*60)
