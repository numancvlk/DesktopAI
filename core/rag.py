#LIBRARIES
import requests
import chromadb
from pathlib import Path
from typing import Any, Dict, List, Optional
from chromadb.config import Settings as ChromaSettings
from .config import get_settings
from .pdf_utils import extract_text_from_pdf, split_text_into_chunks


chroma_client: Optional[chromadb.Client] = None
chroma_collection = None


def get_chroma_collection() -> chromadb.Client:
    global chroma_client, chroma_collection

    if chroma_collection is not None:
        return chroma_collection

    settings = get_settings()
    baseDirectory = Path(settings.rag_pdf_dir)
    persistDirectory = baseDirectory / "index"
    persistDirectory.mkdir(parents=True, exist_ok=True)

    chroma_client = chromadb.PersistentClient(path=str(persistDirecotry))
    chroma_collection = chroma_client.get_or_create_collection(name="pdf_docs")
    return chroma_collection


def init_rag_store() -> None:
    _ = get_chroma_collection()


def embed_text(text: str) -> List[float]:
    if not text:
        raise ValueError("Embedding için metin boş olamaz.")

    settings = get_settings()
    baseUrl = settings.baseUrl.rstrip("/")
    model = settings.rag_embedding_model
    timeout = settings.timeout

    url = f"{baseUrl}/api/embeddings"
    payload = {
        "model": model,
        "prompt": text,
    }

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()

    except requests.RequestException:
        raise RuntimeError("Embedding alma baglanti hatasi")
    except ValueError:
        raise RuntimeError("Embedding yaniti cozulemedi")

    embedding = data.get("embedding")

    if not isinstance(embedding, list):
        raise RuntimeError("Embedding yanıtı geçersiz")

    return embedding


def embed_texts(texts: List[str]) -> List[List[float]]:
    embeddings: List[List[float]] = []

    for t in texts:
        emb = embed_text(t)
        embeddings.append(emb)

    return embeddings


def index_pdf(file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str: #PDFLERI BOLUP DB YE GOTURUYORUZ
    if not file_path:
        raise ValueError("PDF yolu boş olamaz.")

    text = extract_text_from_pdf(file_path)

    if not text:
        raise RuntimeError("PDF'den metin çıkarılamadı.")

    chunks = split_text_into_chunks(text)

    if not chunks:
        raise RuntimeError("PDF ICIN INDEKSLENECEK METIN PARCASI BULUNAMADI.")

    pdfPath = Path(file_path).resolve()
    embeddings = embed_texts(chunks)

    collection = get_chroma_collection()

    base: Dict[str, Any] = {}

    if metadata:
        base.update(metadata)

    base.setdefault("source_path", str(pdfPath))
    base.setdefault("sourceName", pdfPath.name)

    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    for idx in range(len(chunks)):
        meta = dict(base)
        meta["chunkIndex"] = idx
        metadatas.append(meta)
        ids.append(f"{pdfPath.name}_{idx}")

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        embeddings=embeddings,
        ids=ids,
    )

    return str(pdfPath)
 
 
def retrieve_relevant_chunks( #KULLANICININ SORUSUNA ENCOK BENZEYEN PARCALARI GETIRIYOR
    query: str,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:

    if not query or not query.strip():
        return []

    settings = get_settings()
    effectiveK = top_k if top_k is not None else settings.rag_top_k
    
    if effectiveK <= 0:
        return []

    queryEmbedding = embed_text(query)
    collection = get_chroma_collection()

    try:
        result = collection.query(
            queryEmbeddings=[queryEmbedding],
            nResults=effectiveK,
        )
    except:
        raise RuntimeError("RAG sorgusu çalıştırılamadı")

    documents = result.get("documents") or [[]]
    metadatas = result.get("metadatas") or [[]]
    distances = result.get("distances") or [[]]

    if not documents or not documents[0]:
        return []

    chunks: List[Dict[str, Any]] = []

    for text, meta, dist in zip(documents[0], metadatas[0], distances[0]):
        item: Dict[str, Any] = {
            "text": text,
            "metadata": meta or {},
            "distance": dist,
        }
        chunks.append(item)

    return chunks
 
 
def build_augmented_user_input( #kulalnici sorusu ve ragi birlestiriyoz
     user_input: str,
     chunks: List[Dict[str, Any]],
 ) -> str:

     if not chunks:
         return user_input
 
     lines: List[str] = []

     lines.append(
         "Aşağıda PDF'lerden alınmış, soruyla ilgili olabilecek bazı bölümler var. "
         "Uygun olduğunda cevaplarında bu bağlamı kullan."
     )

     lines.append("")
 
     for idx, chunk in enumerate(chunks, start=1):
         meta = chunk.get("metadata") or {}
         sourceName = meta.get("sourceName", "bilinmeyen_kaynak")
         chunkIndex = meta.get("chunkIndex", idx - 1)
         lines.append(f"[BÖLÜM {idx} - Kaynak: {sourceName}, Parça: {chunkIndex}]")
         text = (chunk.get("text") or "").strip()
         lines.append(text)
         lines.append("")
 
     lines.append("Kullanıcı sorusu:")
     lines.append(user_input.strip())
 
     return "\n".join(lines).strip()

def quick_rag_diagnostics( #TEST ICIN TODO SIL BUNU EN SON SIKNITILAR VAR BIRAZ SUAN
    pdfPath: str,
    query: str,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if not pdfPath or not query:
        raise ValueError("pdfPath ve query boş olamaz.")

    _ = index_pdf(pdfPath)

    return retrieve_relevant_chunks(query, top_k=top_k)
 
