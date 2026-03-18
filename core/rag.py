# LIBRARIES
import re
import requests
import chromadb
from pathlib import Path
from typing import Any, Dict, List, Optional
from .config import get_settings
from .pdf_utils import extract_text_from_pdf, split_text_into_chunks


chromaClient: Optional[chromadb.Client] = None
chromaCollection = None

#HYPERPARAMATERS
RETRIEVAL_FETCH = 3
RAG_MAX_CHARS = 5000

TURKISH_NORMALIZE = str.maketrans(
    "çğıöşüÇĞİÖŞÜ",
    "cgiosuCGIOSU",
)


def normalize_for_tokens(text: str) -> str:
    if not text:
        return ""
    return text.strip().lower().translate(TURKISH_NORMALIZE)


def tokenize_overlap(text: str) -> set:
    if not text:
        return set()

    normalized = normalize_for_tokens(text)
    tokens = re.findall(r"[a-z0-9]+", normalized)
    return set(t for t in tokens if len(t) > 1)


def keyword_score(queryTokens: set, chunk_text: str) -> float:
    if not queryTokens:
        return 0.0

    chunkTokens = tokenize_overlap(chunk_text)

    if not chunkTokens:
        return 0.0

    overlap = len(queryTokens & chunkTokens)

    return overlap / len(queryTokens)


def get_chromaCollection() -> chromadb.Client:
    global chromalient, chromaCollection

    if chromaCollection is not None:
        return chromaCollection

    settings = get_settings()
    base_directory = Path(settings.rag_pdf_dir)
    persist_directory = base_directory / "index"
    persist_directory.mkdir(parents=True, exist_ok=True)

    chromalient = chromadb.PersistentClient(path=str(persist_directory))
    chromaCollection = chromalient.get_or_create_collection(name="pdf_docs")
    return chromaCollection


def init_rag_store() -> None:
    _ = get_chromaCollection()


def embed_text(text: str) -> List[float]:
    if not text:
        raise ValueError("Embedding için metin boş olamaz.")

    settings = get_settings()
    base_url = settings.baseUrl.rstrip("/")
    model = settings.rag_embedding_model
    timeout = settings.timeout

    url = f"{base_url}/api/embeddings"
    payload = {
        "model": model,
        "prompt": text,
    }

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        raise RuntimeError("Embedding alma hatasi")
    except ValueError:
        raise RuntimeError("Embedding yaniti cozulemedi")

    embedding = data.get("embedding")
    if not isinstance(embedding, list):
        raise RuntimeError("Embedding geçersiz")
    return embedding


def embed_texts(texts: List[str]) -> List[List[float]]:
    return [embed_text(t) for t in texts]


def index_pdf(file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    if not file_path:
        raise ValueError("PDF yolu boş olamaz.")

    text = extract_text_from_pdf(file_path)
    if not text:
        raise RuntimeError("PDF'den metin çıkarılamadı.")

    chunks = split_text_into_chunks(text)
    if not chunks:
        raise RuntimeError("PDF için indekslenecek metin parçası bulunamadı.")

    pdfPath = Path(file_path).resolve()

    def norm(s: str) -> str:
        t = normalize_for_tokens(s)
        return t if t else s

    embeddings = embed_texts([norm(c) for c in chunks])
    collection = get_chromaCollection()

    base: Dict[str, Any] = dict(metadata) if metadata else {}
    base.setdefault("source_path", str(pdfPath))
    base.setdefault("sourceName", pdfPath.name)

    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    for idx, chunk in enumerate(chunks):
        meta = {**base, "chunkIndex": idx}
        metadatas.append(meta)
        ids.append(f"{pdfPath.name}_{idx}")

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        embeddings=embeddings,
        ids=ids,
    )
    return str(pdfPath)


def retrieve_relevant_chunks(
    query: str,
    top_k: Optional[int] = None,
    max_distance: Optional[float] = None,
    use_rerank: bool = True,
) -> List[Dict[str, Any]]:
    if not query or not query.strip():
        return []

    settings = get_settings()
    effectiveK = top_k if top_k is not None else settings.rag_top_k
    effectiveK = max(effectiveK, 6)
    if effectiveK <= 0:
        return []

    fetchK = min(50, max(effectiveK * RETRIEVAL_FETCH, effectiveK + 5))
    queryEmbed = normalize_for_tokens(query) or query
    queryEmbedding = embed_text(queryEmbed)
    collection = get_chromaCollection()

    try:
        result = collection.query(
            query_embeddings=[queryEmbedding],
            n_results=fetchK,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        raise RuntimeError("RAG sorgusu çalıştırılamadı")

    documents = result.get("documents") or [[]]
    metadatas = result.get("metadatas") or [[]]
    distances = result.get("distances") or [[]]

    if not documents or not documents[0]:
        return []

    queryTokens = tokenize_overlap(query)
    candidates: List[Dict[str, Any]] = []

    for text, meta, dist in zip(documents[0], metadatas[0], distances[0]):
        if max_distance is not None and dist is not None and dist > max_distance:
            continue
        item: Dict[str, Any] = {
            "text": text,
            "metadata": meta or {},
            "distance": dist,
        }
        if use_rerank and queryTokens:
            item["_keyword_score"] = keyword_score(queryTokens, text)
        else:
            item["_keyword_score"] = 0.0
        candidates.append(item)

    if use_rerank and queryTokens:
        candidates.sort(
            key=lambda x: (-x.get("_keyword_score", 0.0), x.get("distance") or 999.0)
        )

    resultList: List[Dict[str, Any]] = []
    for item in candidates[:effectiveK]:
        item.pop("_keyword_score", None)
        resultList.append(item)
    resultList.sort(
        key=lambda x: (
            (x.get("metadata") or {}).get("sourceName", ""),
            (x.get("metadata") or {}).get("chunkIndex", 0),
        )
    )
    return resultList


def build_augmented_user_input(
    user_input: str,
    chunks: List[Dict[str, Any]],
    max_context_chars: Optional[int] = None,
) -> str:
    if not chunks:
        return user_input.strip()

    sortedC = sorted(
        chunks,
        key=lambda c: (
            (c.get("metadata") or {}).get("sourceName", ""),
            (c.get("metadata") or {}).get("chunkIndex", 0),
        ),
    )

    limit = max_context_chars if max_context_chars is not None else RAG_MAX_CHARS
    lines: List[str] = []
    lines.append(
        "Aşağıdaki KAYNAK METİN bölümleri, sorunun cevabı için VERİLEN TEK KAYNAKTIR. "
        "Cevabını SADECE bu metne dayanarak ver. Bu metinde olmayan hiçbir bilgiyi ekleme veya tahmin etme."
    )
    lines.append("")
    lines.append("--- KAYNAK METİN ---")
    lines.append("")

    total = 0
    for idx, chunk in enumerate(sortedC, start=1):
        meta = chunk.get("metadata") or {}
        sourceName = meta.get("sourceName", "PDF")
        chunkIndex = meta.get("chunkIndex", idx - 1)
        text = (chunk.get("text") or "").strip()

        if not text:
            continue

        block = f"[Parça {idx} | Kaynak: {sourceName}]\n{text}"
        blockLen = len(block) + 2

        if total + blockLen > limit:
            break
        lines.append(block)
        lines.append("")
        total += blockLen

    lines.append("--- KAYNAK METİN SONU ---")
    lines.append("")
    lines.append("Kullanıcı sorusu (cevabını YALNIZCA yukarıdaki kaynak metne göre ver):")
    lines.append(user_input.strip())

    return "\n".join(lines).strip()


def quick_rag_diagnostics(
    pdfPath: str,
    query: str,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if not pdfPath or not query:
        raise ValueError("pdfPath ve query boş olamaz.")
    _ = index_pdf(pdfPath)
    return retrieve_relevant_chunks(query, top_k=top_k)
