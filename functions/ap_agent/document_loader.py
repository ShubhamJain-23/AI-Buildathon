"""Enterprise Document Ingestion Engine for Quotations and Vendor Bids.
Extracts unstructured textual data and line items across diverse enterprise formats:
- PDF (.pdf)
- Spreadsheets / Excel (.xlsx, .xls, .csv)
- Word Documents (.docx, .doc)
- Presentations / Slides (.pptx, .ppt)
- Markdown & Text (.md, .txt)
- Images (.png, .jpg, .jpeg, .webp) via Gemini Multimodal Vision / OCR
"""
import io
import re
import os
import zipfile
import zlib
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List

def extract_text_from_bytes(filename: str, data: bytes, gemini_api_key: Optional[str] = None) -> str:
    """Extracts text content from binary file bytes based on file format."""
    ext = os.path.splitext(filename)[1].lower()

    if ext in [".txt", ".md", ".markdown", ".csv", ".json"]:
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="ignore")

    elif ext == ".docx":
        return _extract_docx(data)

    elif ext == ".pptx":
        return _extract_pptx(data)

    elif ext in [".xlsx", ".xlsm"]:
        return _extract_xlsx(data)

    elif ext == ".pdf":
        return _extract_pdf(data, gemini_api_key=gemini_api_key)

    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".tiff"]:
        return _extract_image(data, gemini_api_key=gemini_api_key)

    else:
        # Fallback raw byte scanning
        try:
            return data.decode("utf-8")
        except Exception:
            return data.decode("latin-1", errors="ignore")

def _extract_docx(data: bytes) -> str:
    """Extracts text from DOCX (Office Open XML) without external binary dependencies."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if "word/document.xml" not in z.namelist():
                return ""
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            # w:t elements contain text
            paragraphs = []
            for p in tree.iter():
                if p.tag.endswith("}p"):
                    texts = [node.text for node in p.iter() if node.tag.endswith("}t") and node.text]
                    if texts:
                        paragraphs.append("".join(texts))
            return "\n".join(paragraphs)
    except Exception as e:
        return f"[DOCX Extraction Fallback: {e}]\n" + data.decode("latin-1", errors="ignore")

def _extract_pptx(data: bytes) -> str:
    """Extracts text from PPTX slides (Office Open XML)."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            slide_texts = []
            slide_names = sorted([n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")])
            for sname in slide_names:
                xml_content = z.read(sname)
                tree = ET.fromstring(xml_content)
                texts = [node.text for node in tree.iter() if node.tag.endswith("}t") and node.text]
                if texts:
                    slide_texts.append(" ".join(texts))
            return "\n\n".join(slide_texts)
    except Exception as e:
        return f"[PPTX Extraction Fallback: {e}]\n" + data.decode("latin-1", errors="ignore")

def _extract_xlsx(data: bytes) -> str:
    """Extracts tabular data from XLSX worksheet into CSV-formatted text."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            # 1. Read shared strings if present
            shared_strings = []
            if "xl/sharedStrings.xml" in z.namelist():
                tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                for si in tree.iter():
                    if si.tag.endswith("}si"):
                        t_parts = [node.text for node in si.iter() if node.tag.endswith("}t") and node.text]
                        shared_strings.append("".join(t_parts))

            # 2. Read first worksheet
            sheet_name = "xl/worksheets/sheet1.xml"
            if sheet_name not in z.namelist():
                sheets = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
                if sheets:
                    sheet_name = sheets[0]
                else:
                    return ""

            sheet_tree = ET.fromstring(z.read(sheet_name))
            rows = []
            for row in sheet_tree.iter():
                if row.tag.endswith("}row"):
                    cell_vals = []
                    for c in row.iter():
                        if c.tag.endswith("}c"):
                            cell_type = c.get("t")
                            v_elem = next((node for node in c.iter() if node.tag.endswith("}v")), None)
                            if v_elem is not None and v_elem.text:
                                val = v_elem.text
                                if cell_type == "s":
                                    idx = int(val)
                                    val = shared_strings[idx] if idx < len(shared_strings) else val
                                cell_vals.append(str(val))
                    if cell_vals:
                        rows.append("  ".join(cell_vals))
            return "\n".join(rows)
    except Exception as e:
        return f"[XLSX Extraction Fallback: {e}]\n" + data.decode("latin-1", errors="ignore")

def _extract_pdf(data: bytes, gemini_api_key: Optional[str] = None) -> str:
    """Extracts text streams and FlateDecode blocks from PDF."""
    text_fragments = []

    # 1. Check if Gemini Vision OCR is available
    key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([
                {"mime_type": "application/pdf", "data": data},
                "Extract all text, line items, item names, quantities, unit prices, total amounts, warranty, and delivery terms from this quotation PDF accurately."
            ])
            if response and response.text:
                return response.text
        except Exception:
            pass

    # 2. Deterministic stream decompressor for standard PDFs
    stream_matches = re.findall(b"stream[\r\n]+(.*?)[\r\n]+endstream", data, re.DOTALL)
    for s in stream_matches:
        decompressed = None
        try:
            decompressed = zlib.decompress(s)
        except Exception:
            try:
                decompressed = zlib.decompress(s, -zlib.MAX_WBITS)
            except Exception:
                decompressed = s

        if decompressed:
            # Look for Tj or TJ text blocks: (text) Tj or [(t1) 10 (t2)] TJ
            tjs = re.findall(rb"\((.*?)\)\s*Tj", decompressed)
            for t in tjs:
                try:
                    text_fragments.append(t.decode("utf-8", errors="ignore"))
                except Exception:
                    pass

            tjs_arr = re.findall(rb"\[(.*?)\]\s*TJ", decompressed)
            for arr in tjs_arr:
                inner = re.findall(rb"\((.*?)\)", arr)
                for t in inner:
                    try:
                        text_fragments.append(t.decode("utf-8", errors="ignore"))
                    except Exception:
                        pass

    if text_fragments:
        return " ".join(text_fragments)

    # 3. Fallback raw string matching
    raw_strings = re.findall(rb"[\x20-\x7E]{4,}", data)
    return "\n".join(s.decode("latin-1", errors="ignore") for s in raw_strings)

def _extract_image(data: bytes, gemini_api_key: Optional[str] = None) -> str:
    """Extracts text from quotation image via Gemini Multimodal Vision API."""
    key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([
                {"mime_type": "image/jpeg", "data": data},
                "Extract all quotation text, vendor name, line items, quantity, price, delivery lead time, and warranty terms from this image."
            ])
            if response and response.text:
                return response.text
        except Exception:
            pass

    return "[Image Quotation Attached - OCR extraction requires Gemini API key]"
