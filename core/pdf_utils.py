#LIBRARIES
import os
from pathlib import Path
from typing import List
from pypdf import PdfReader
 

def extract_text_from_pdf(file_path: str) -> str: #PDFI STRINGE CEVIRME
     if not file_path:
         raise ValueError("PDF yolu boş olamaz.")
 
     path = Path(file_path)

     if not path.is_file():
         raise FileNotFoundError(f"PDF dosyası bulunamadı")
 
     if path.suffix.lower() != ".pdf":
         raise ValueError("Sadece .pdf uzantılı dosyalar desteklenmektedir.")
 
     try:
         reader = PdfReader(str(path))
     except:
         raise RuntimeError(f"PDF okunamadı")
 
     texts: List[str] = []
     
     for page in reader.pages:
         try:
             pageText = page.extract_text() or ""
         except Exception:
             pageText = ""
         if pageText.strip():
             texts.append(pageText.strip())
 
     return "\n\n".join(texts).strip()
 
 
def split_text_into_chunks( #RAG ICIN METNI BOLUYOM
     text: str,
     max_chars: int = 800, #Karakter bazli yaptik uzun pdflerde sorun cikarabilir TODO tokenlere gore ayarlariz ilerde eger sorun cikarirsa 
     overlap: int = 100,
 ) -> List[str]:

     if max_chars <= 0:
         raise ValueError("max_chars pozitif olmalıdır.")

     if overlap < 0:
         raise ValueError("overlap negatif olamaz.")

     if overlap >= max_chars:
         raise ValueError("overlap, max_chars değerinden küçük olmalıdır.")
 
     if not text:
         return []
 
     cleaned = text.strip()

     if not cleaned:
         return []
 
     chunks: List[str] = []
     start = 0
     length = len(cleaned)
 
     while start < length: 
         end = min(start + max_chars, length)

         chunk = cleaned[start:end].strip()

         if chunk:
             chunks.append(chunk)

         if end == length:
             break

         start = max(0, end - overlap)
 
     return chunks
 
