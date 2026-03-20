# LIBRARIES
import re
from pathlib import Path
from typing import List
from pypdf import PdfReader

ROW_STARTER_PATTERN = re.compile( #SATIR BASLANGICI ICIN AMAA ICIME COK SINMEDI BU DEGISEBILIR
    r"^(?:\s*)(?:Pazartesi|Salı|Sali|Çarşamba|Carsamba|Perşembe|Persembe|Cuma|Cumartesi|Pazar|\d{1,2}\s*:\s*\d{2})",
    re.IGNORECASE,
)

def normalize_blanks(text: str) -> str: #PDF den gelen metnon bosluklarini yeni satirlarini vs temizliyor bazen kotu bolundukleri icin
    if not text:
        return ""

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_text(file_path: str) -> str: #PDF icinden metni aliyor normalize_blanks ile temizliyor donduruyor
    if not file_path:
        raise ValueError("PDF dosyasiy yok")

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError("PDF dosyasi yok")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Sadece .pdf uzantılı dosyalar ile calisabilir.")

    try:
        reader = PdfReader(str(path))
    except Exception:
        raise RuntimeError("PDF okunamadi")

    texts: List[str] = []

    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        page_text = normalize_blanks(page_text)
        if page_text:
            texts.append(page_text)

    if not texts:
        return ""

    full = "\n\n".join(texts)
    return normalize_blanks(full)


def sentence_split(text: str) -> List[str]: #Metni son isaretlere yani noktalamaya gore boluyo iste
    if not text.strip():
        return []

    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def split_paragraphs(text: str) -> List[str]: #Paragraflari kabul ediyor yani algiliyor aslinda
    if not text.strip():
        return []
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def split_table(text: str) -> List[str]: #tablolari ayirmak icin ama tam calismiyor #TODO duzeltilebilir
    if not text or not text.strip():
        return []

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    if not lines:
        return []

    rows: List[str] = []
    current: List[str] = []

    for line in lines:
        if ROW_STARTER_PATTERN.match(line):
            if current:
                rows.append(" ".join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        rows.append(" ".join(current))

    if len(rows) == 1 and len(rows[0]) > 400:
        parts = re.split(r"\s+(?=Pazartesi|Salı|Sali|Çarşamba|Carsamba|Perşembe|Persembe|Cuma|Cumartesi|Pazar)(?=\s|$)", rows[0], flags=re.IGNORECASE)

        if len(parts) > 1:
            rows = [p.strip() for p in parts if p.strip()]

    return rows


def chunk_table(rows: List[str], max_chars: int, overlap: int, min_chars: int) -> List[str]: #tablolari chunklara boluyor
    if not rows:
        return []

    chunks: List[str] = []
    buffer: List[str] = []
    bufferLen = 0

    for row in rows:
        rowLen = len(row) + (1 if buffer else 0)

        if bufferLen + rowLen <= max_chars:
            buffer.append(row)
            bufferLen += rowLen
        else:
            if buffer:
                chunk = " ".join(buffer)
                if len(chunk) >= min_chars or not chunks:
                    chunks.append(chunk)
                overlapT = ""

                if overlap > 0 and len(chunk) > overlap:
                    overlapT = chunk[-overlap:].strip()
                    firstBlank = overlapT.find(" ")

                    if firstBlank > 0:
                        overlapT = overlapT[firstBlank:].strip()
                buffer = [overlapT, row] if overlapT else [row]
                bufferLen = len(overlapT) + len(row) + (2 if overlapT else 0)
            else:
                buffer = [row]
                bufferLen = len(row)

    if buffer:
        chunk = " ".join(buffer).strip()

        if chunk and (len(chunk) >= min_chars or not chunks):
            chunks.append(chunk)
    return [c for c in chunks if c]


def split_text_chunks( #Ana kisim burasi tum islemler burda birlesiyor gibi dusunun
    text: str,
    max_chars: int = 700,
    overlap: int = 120,
    min_chars: int = 100,
) -> List[str]:

    if max_chars <= 0:
        raise ValueError("max_chars pozitif olmalıdır.")

    if overlap < 0:
        raise ValueError("overlap negatif olamaz.")

    if overlap >= max_chars:
        raise ValueError("overlap, max_chars değerinden küçük olmalıdır.")

    if not text or not text.strip():
        return []

    cleaned = normalize_blanks(text)

    if not cleaned:
        return []

    paragraphs = split_paragraphs(cleaned)

    if not paragraphs:
        paragraphs = [cleaned]

    if len(paragraphs) == 1 and len(paragraphs[0]) > max_chars:
        para = paragraphs[0]
        sentenceEnds = len(re.findall(r"[.!?]", para))
        if sentenceEnds < 2 and "\n" in para:
            rows = split_table(para)
            if rows:
                return chunk_table(rows, max_chars, overlap, min_chars)

    units: List[str] = []
    
    for para in paragraphs:
        if len(para) <= max_chars:
            units.append(para)
        else:
            sentences = sentence_split(para)
            curren #Metni son isaretlere yani noktalamaya gore boluyo istet
            currentLen = 0

            for sent in sentences:
                sentLen = len(sent) + 1
                if currentLen + sentLen > max_chars and current:
                    units.append(" ".join(current))
                    overlapLen = 0
                    overlapSen: List[str] = []
                    for s in reversed(current):
                        if overlapLen + len(s) + 1 <= overlap:
                            overlapSen.append(s)
                            overlapLen += len(s) + 1
                        else:
                            break
                    current = list(reversed(overlapSen))
                    currentLen = sum(len(s) + 1 for s in current) - 1
                current.append(sent)
                currentLen += sentLen
            if current:
                units.append(" ".join(current))

    chunks: List[str] = []
    buffer: List[str] = []
    bufferLen = 0

    for unit in units:
        needBlank = 1 if buffer else 0
        unitLen = len(unit) + needBlank

        if bufferLen + unitLen <= max_chars:
            if buffer:
                buffer.append(unit)
                bufferLen += len(unit) + 1
            else:
                buffer = [unit]
                bufferLen = len(unit)
        else:
            if buffer:
                chunk = " ".join(buffer)
                if len(chunk) >= min_chars or not chunks:
                    chunks.append(chunk)
                overlapText = ""
                if overlap > 0 and len(chunk) > overlap:
                    overlapText = chunk[-overlap:].strip()
                    firstBlank = overlapText.find(" ")
                    if firstBlank > 0:
                        overlapText = overlapText[firstBlank:].strip()
                buffer = [overlapText, unit] if overlapText else [unit]
                bufferLen = len(overlapText) + len(unit) + (2 if overlapText else 0)
            else:
                buffer = [unit]
                bufferLen = len(unit)

    if buffer:
        chunk = " ".join(buffer).strip()
        if chunk and (len(chunk) >= min_chars or not chunks):
            chunks.append(chunk)

    return [c for c in chunks if c]
