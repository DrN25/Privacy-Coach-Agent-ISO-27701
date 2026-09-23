import pymupdf as fitz
import json
import re
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

PIPELINES_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.dirname(PIPELINES_DIR)
BASE_DIR = os.path.dirname(KB_DIR)
DATASETS_DIR = os.path.join(KB_DIR, "datasets")

PDF_DIR = os.path.join(BASE_DIR, "fuentes_normativas_pdf")
if not os.path.exists(PDF_DIR):
    PDF_DIR = KB_DIR

SANCTIONS_PDF = os.path.join(PDF_DIR, "05_ANPD_Registro_Oficial_Sanciones_Impuestas.pdf")
if not os.path.exists(SANCTIONS_PDF):
    SANCTIONS_PDF = os.path.join(PDF_DIR, "1255336-registro-de-sanciones-impuestas.pdf")

SANCTIONS_OUT = os.path.join(DATASETS_DIR, "anpd_sanciones_dataset.json")

def parse_uit_values(multa_text):
    """Extracts all individual UIT float values from text, e.g. '7,50 UIT\n9,75 UIT' -> [7.5, 9.75]"""
    if not multa_text:
        return []
    matches = re.findall(r"(\d+[\,\.]?\d*)\s*UIT", multa_text, re.IGNORECASE)
    results = []
    for m in matches:
        try:
            val = float(m.replace(",", "."))
            results.append(val)
        except ValueError:
            pass
    return results

def split_resoluciones(res_text):
    """Splits multiple resolutions in a single cell into a list."""
    if not res_text:
        return []
    # Split by pattern 'Resolución Directoral' or 'Resolución'
    parts = re.split(r"(?=(?:Resoluci[oó]n\s+(?:Directoral|N[°ºo\.])))", res_text, flags=re.IGNORECASE)
    cleaned = [p.replace("\n", " ").strip() for p in parts if p.strip() and len(p.strip()) > 10]
    return cleaned if cleaned else [res_text.replace("\n", " ").strip()]

def split_infracciones(infracciones_raw_list):
    """Splits and structures multiple infractions."""
    all_raw_text = "\n".join(infracciones_raw_list)
    # Split by 'Artículo' or 'Art.' or bullet markers
    parts = re.split(r"(?=(?:Art[ií]culo\s+\d+|[a-z]\.\s+(?:Dar|No|Obstruir|Realizar|Incumplir|Crear)))", all_raw_text, flags=re.IGNORECASE)
    
    infracciones_clean = []
    for p in parts:
        p_clean = p.replace("\n", " ").strip()
        if len(p_clean) > 15:
            # Extract legal article if present
            m_art = re.search(r"(Art[ií]culo\s+\d+[^a-z0-9]*(?:numeral\s+\d+)?[^a-z0-9]*(?:literal\s+[a-z])?)", p_clean, re.IGNORECASE)
            art_code = m_art.group(1).strip() if m_art else "LPDP / Reglamento"
            
            infracciones_clean.append({
                "articulo_referencia": art_code,
                "texto_infraccion": p_clean
            })
            
    if not infracciones_clean and all_raw_text.strip():
        infracciones_clean.append({
            "articulo_referencia": "LPDP / Reglamento",
            "texto_infraccion": all_raw_text.replace("\n", " ").strip()
        })
    return infracciones_clean

def split_medidas_correctivas(medidas_text):
    """Splits corrective measures by Roman numerals (I., II.), bullets (•), or numbers (1., 2.)."""
    if not medidas_text or not medidas_text.strip():
        return []
    
    # Clean Smartfit overlapping OCR artifact if detected
    text = re.sub(r"q\s+Inu\s+ce\s+p\s+iro\s+ed\s+nr[^\n]+", "", medidas_text)
    
    # Split by Roman numerals I., II., III. or bullets • or numbers 1., 2.
    parts = re.split(r"(?=(?:(?:[IVX]+\.|\•|\-|\d+\.)\s+))", text)
    cleaned = []
    for p in parts:
        clean_p = p.replace("\n", " ").strip()
        # remove prefix like "Imponer como medida correctiva la siguiente:"
        clean_p = re.sub(r"^Imponer\s+como\s+medida\s+correctiva\s+la\s+siguiente:?\s*", "", clean_p, flags=re.IGNORECASE)
        if clean_p and len(clean_p) > 10:
            cleaned.append(clean_p)
            
    if not cleaned and medidas_text.strip():
        clean_p = re.sub(r"^Imponer\s+como\s+medida\s+correctiva\s+la\s+siguiente:?\s*", "", medidas_text.replace("\n", " ").strip(), flags=re.IGNORECASE)
        if clean_p:
            cleaned.append(clean_p)
            
    return cleaned

def parse_all_sanctions_advanced():
    print("Iniciando parseo avanzado de 85 páginas...")
    doc = fitz.open(SANCTIONS_PDF)
    consolidated_entities = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        tabs = page.find_tables()
        for tab in tabs.tables:
            rows = tab.extract()
            data_rows = rows[1:] if page_idx == 0 else rows
            
            current_entity = None
            
            for r in data_rows:
                entidad = (r[1] or "").replace("\n", " ").strip() if len(r) > 1 else ""
                
                # If new entity header detected
                if entidad and not entidad.startswith("Entidad") and not entidad.startswith("N"):
                    current_entity = {
                        "pagina_pdf": page_idx + 1,
                        "entidad": entidad,
                        "ruc": (r[2] or "").replace("\n", " ").strip() if len(r) > 2 and r[2] and r[2].strip() else None,
                        "resoluciones_raw": r[3] or "",
                        "infracciones_raw": [r[4].strip()] if len(r) > 4 and r[4] and r[4].strip() else [],
                        "multas_raw": r[5] or "",
                        "medidas_raw": r[6] or "" if len(r) > 6 else ""
                    }
                    consolidated_entities.append(current_entity)
                elif current_entity is not None:
                    # Merged continuation row!
                    if len(r) > 3 and r[3] and r[3].strip():
                        current_entity["resoluciones_raw"] += "\n" + r[3].strip()
                    if len(r) > 4 and r[4] and r[4].strip():
                        current_entity["infracciones_raw"].append(r[4].strip())
                    if len(r) > 5 and r[5] and r[5].strip():
                        current_entity["multas_raw"] += "\n" + r[5].strip()
                    if len(r) > 6 and r[6] and r[6].strip():
                        current_entity["medidas_raw"] += "\n" + r[6].strip()

    # Now format each consolidated entity into a rich JSON structure
    final_dataset = []
    
    for idx, item in enumerate(consolidated_entities):
        uit_list = parse_uit_values(item["multas_raw"])
        total_uit = round(sum(uit_list), 2) if uit_list else None
        
        resoluciones = split_resoluciones(item["resoluciones_raw"])
        infracciones = split_infracciones(item["infracciones_raw"])
        medidas = split_medidas_correctivas(item["medidas_raw"])
        
        # Classify sector
        ent_lower = item["entidad"].lower()
        sector = "General / Comercio"
        if any(k in ent_lower for k in ["clinica", "salud", "hospital", "medico", "sante", "dental"]):
            sector = "Salud / Clínica"
        elif any(k in ent_lower for k in ["banco", "financier", "ripley", "credito", "interbank", "scotia", "caja rural"]):
            sector = "Financiero / Banca"
        elif any(k in ent_lower for k in ["universidad", "colegio", "educat", "instituto"]):
            sector = "Educación"
        elif any(k in ent_lower for k in ["http", "www", ".org", ".com", ".pe", "online", "datosperu"]):
            sector = "Internet / Web / Plataforma"
        elif any(k in ent_lower for k in ["supermercado", "tienda", "retail", "s.a.c."]):
            sector = "Retail / Comercio"
            
        # Pair infraccion with multa if counts match
        if len(infracciones) == len(uit_list):
            for i in range(len(infracciones)):
                infracciones[i]["multa_uit"] = uit_list[i]
        elif len(uit_list) == 1:
            for inf in infracciones:
                inf["multa_uit"] = uit_list[0]
                
        final_dataset.append({
            "id": idx + 1,
            "pagina_pdf": item["pagina_pdf"],
            "entidad": item["entidad"],
            "ruc": item["ruc"],
            "sector": sector,
            "resoluciones": resoluciones,
            "infracciones": infracciones,
            "multas_desglose_uit": uit_list,
            "multa_total_uit": total_uit,
            "medidas_correctivas": medidas
        })
        
    with open(SANCTIONS_OUT, "w", encoding="utf-8") as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)
        
    print(f"-> Parsed {len(final_dataset)} entities into rich JSON.")
    return final_dataset

if __name__ == "__main__":
    data = parse_all_sanctions_advanced()
    # Print Smartfit, Cencosud, and DatosPeru to verify
    for item in data:
        if any(k in item["entidad"] for k in ["SMARTFIT", "CENCOSUD SCOTIA", "DATOSPERU"]):
            print("="*60)
            print(json.dumps(item, ensure_ascii=False, indent=2))
