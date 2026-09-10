import sys
import json
import re
import uuid
import hashlib
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import (
    init_gemini,
    FAST_MODEL_NAME,
    EMBEDDING_MODEL_NAME,
    CHROMA_DB_DIR,
    COLLECTION_NAME,
    DOCSTORE_DIR,
    PROPOSITION_MAX_PER_CHUNK,
    PROPOSITION_MIN_WORDS,
    PROPOSITION_BATCH_SIZE,
    call_grok_chat,
    is_grok_available,
)
import google.generativeai as genai
import chromadb

init_gemini()

DOCS_DIR = CURRENT_DIR / "docs"


# ════════════════════════════════════════════════════════════════════
# Data model
# ════════════════════════════════════════════════════════════════════
@dataclass
class ParentChunk:
    doc_id: str
    content: str
    source_file: str
    category: str
    section: str
    propositions: List[str] = field(default_factory=list)


def make_doc_id(content: str) -> str:
    """Tao doc_id duy nhat dua tren SHA-256 cua noi dung (Deterministic & O(1))."""
    normalized = " ".join(content.strip().split())
    return "doc_" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


# ════════════════════════════════════════════════════════════════════
# Buoc 1: Parse Documents -> Parent Chunks
# ════════════════════════════════════════════════════════════════════
def parse_documents(docs_dir: Path = DOCS_DIR) -> List[ParentChunk]:
    """
    Doc tat ca file *.md va tach thanh parent chunks theo heading ##.
    Moi section (## heading) la 1 parent chunk doc lap.
    """
    chunks: List[ParentChunk] = []
    md_files = sorted(docs_dir.glob("*.md"))
    if not md_files:
        print(f"WARNING: Khong tim thay file .md trong {docs_dir}")
        return chunks

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8").strip()
        lines = text.splitlines()

        current_category = md_file.stem
        current_section = ""
        current_lines: List[str] = []

        def flush_chunk():
            content = "\n".join(current_lines).strip()
            if content and len(content.split()) >= PROPOSITION_MIN_WORDS:
                chunks.append(ParentChunk(
                    doc_id=make_doc_id(content),
                    content=content,
                    source_file=md_file.name,
                    category=current_category,
                    section=current_section,
                ))

        for line in lines:
            if line.startswith("# ") and not line.startswith("## "):
                flush_chunk()
                current_category = line[2:].strip()
                current_section = ""
                current_lines = []
            elif line.startswith("## "):
                flush_chunk()
                current_section = line.strip()
                current_lines = []
            else:
                if line.strip():
                    current_lines.append(line)

        flush_chunk()

    return chunks


# ════════════════════════════════════════════════════════════════════
# Buoc 2: Decompose Parent Chunk -> Propositions
# ════════════════════════════════════════════════════════════════════
_DECOMPOSE_PROMPT = (
    "Ban la chuyen gia phan tich van ban ky thuat cho ung dung ChatMessageE2E.\n\n"
    "NHIEM VU:\n"
    "Phan tach doan van sau thanh danh sach cac menh de (propositions).\n"
    "Moi menh de phai:\n"
    "  - La mot cau hoan chinh, ngan gon, doc lap.\n"
    "  - Chua dung 1 su that / khai niem cu the.\n"
    "  - Co the hieu dung nghia ma KHONG can doc them ngu canh xung quanh.\n"
    "  - Giu nguyen thuat ngu ky thuat (ECDH, AES-256-GCM, JWT, OAuth2...).\n"
    "  - Khong dung dau ngoac kep ben trong menh de (thay bang dau nhay don neu can).\n\n"
    "DOAN VAN (Danh muc: {category} | Phan: {section}):\n"
    '\"\"\"{content}\"\"\"\n\n'
    "OUTPUT BAT BUOC: Chi tra ve mot JSON array cac chuoi, vi du:\n"
    '["Menh de 1.", "Menh de 2.", "Menh de 3."]\n'
    "Khong them bat ky giai thich hay markdown code block nao khac."
)


def decompose_to_propositions(chunk: ParentChunk, verbose: bool = False) -> List[str]:
    """
    Phan tach 1 parent chunk thanh danh sach propositions:
      1. Uu tien dung Groq Cloud (nhanh, khong ton quota Gemini).
      2. Neu Groq khong co/loi, dung Gemini voi co che retry backoff khi cham quota 429.
      3. Fallback: Tu dong tach cau bang regex tu doan van goc.
    """
    prompt = _DECOMPOSE_PROMPT.format(
        category=chunk.category,
        section=chunk.section,
        content=chunk.content,
    )

    parsed: Optional[List[str]] = None
    raw_text = ""

    # Uu tien 1: Dung Groq neu co API key (tiet kiem hoan toan quota Gemini)
    if is_grok_available():
        try:
            res_groq = call_grok_chat(
                prompt=prompt,
                system_instruction="Ban la chuyen gia trich xuat thong tin. Chi tra ve duy nhat 1 JSON array cac chuoi.",
                temperature=0.1,
                max_tokens=1024,
                timeout=20.0,
            )
            if res_groq:
                raw_text = res_groq.strip()
                if verbose:
                    print("     [Decompose] Dung Groq Cloud (tiet kiem Gemini quota)")
        except Exception as e:
            if verbose:
                print(f"     i [Indexer] Groq decompose gap loi: {e}. Chuyen sang Gemini...")

    # Uu tien 2: Dung Gemini voi co che Retry Backoff khi cham quota 429
    if not raw_text:
        max_gemini_retries = 3
        delay = 10.0
        for attempt in range(1, max_gemini_retries + 1):
            try:
                model = genai.GenerativeModel(
                    model_name=FAST_MODEL_NAME,
                    generation_config={
                        "temperature": 0.1,
                        "max_output_tokens": 1024,
                        "response_mime_type": "application/json",
                    },
                )
                response = model.generate_content(prompt)
                raw_text = response.text.strip()
                break
            except Exception as e:
                err_msg = str(e).lower()
                is_quota = "quota" in err_msg or "429" in err_msg or "resourceexhausted" in err_msg or "rate limit" in err_msg
                if is_quota and attempt < max_gemini_retries:
                    print(f"     [Gemini Rate Limit] Cham 429 o buoc Decompose. Nghi {delay:.0f}s roi thu lai (Lan {attempt}/{max_gemini_retries})...")
                    time.sleep(delay)
                    delay *= 1.5
                else:
                    if verbose:
                        print(f"     [Indexer] Gemini sinh propositions gap loi: {e}")
                    break

    # Parse JSON tu raw_text
    if raw_text:
        if "```" in raw_text:
            for part in raw_text.split("```"):
                part = part.strip().lstrip("json").strip()
                if part.startswith("["):
                    raw_text = part
                    break

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r'\[\s*".*?"\s*\]', raw_text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except Exception:
                    pass

    # Fallback 3: Neu khong lay duoc tu LLM nao, tach cau tu nhien tu doan goc
    if not isinstance(parsed, list) or not parsed:
        if verbose:
            print(f"     i [Indexer] Fallback: Tach cau tu dong tu Parent Chunk ({chunk.section})")
        clean_text = chunk.content.replace("\n", " ").replace("**", "").replace("*", "")
        parsed = [
            s.strip() + "." for s in clean_text.split(".")
            if len(s.strip().split()) >= PROPOSITION_MIN_WORDS
        ]
        if not parsed:
            parsed = [chunk.content]

    seen = set()
    filtered: List[str] = []
    for p in parsed:
        p_clean = str(p).strip()
        p_lower = p_clean.lower()
        if len(p_clean.split()) >= PROPOSITION_MIN_WORDS and p_lower not in seen:
            seen.add(p_lower)
            filtered.append(p_clean)
            if len(filtered) >= PROPOSITION_MAX_PER_CHUNK:
                break

    if not filtered:
        filtered = [chunk.content]

    if verbose:
        print(f"     -> Sinh duoc {len(filtered)} propositions")

    return filtered


# ════════════════════════════════════════════════════════════════════
# Buoc 3a: DocStore — luu / doc full parent chunk theo doc_id
# ════════════════════════════════════════════════════════════════════
def get_docstore_dir() -> Path:
    DOCSTORE_DIR.mkdir(parents=True, exist_ok=True)
    return DOCSTORE_DIR


def save_to_docstore(doc_id: str, content: str, docstore_dir: Path) -> bool:
    """
    Luu full parent chunk thanh file JSON: {doc_id}.json.
    Tra ve True neu da luu moi, False neu noi dung da ton tai tu truoc (skip).
    """
    file_path = docstore_dir / f"{doc_id}.json"
    if file_path.exists():
        return False
    file_path.write_text(
        json.dumps({"doc_id": doc_id, "content": content}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return True


def load_from_docstore(doc_id: str, docstore_dir: Optional[Path] = None) -> Optional[str]:
    """Tra cuu full parent chunk tu DocStore theo doc_id. Tra ve None neu khong co."""
    if docstore_dir is None:
        docstore_dir = DOCSTORE_DIR
    file_path = docstore_dir / f"{doc_id}.json"
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8")).get("content")


def clear_docstore(docstore_dir: Path):
    if docstore_dir.exists():
        for f in docstore_dir.glob("*.json"):
            f.unlink()
    print(f"[DocStore] Da xoa sach {docstore_dir}")


# ════════════════════════════════════════════════════════════════════
# Buoc 3b: ChromaDB — embed propositions + upsert
# ════════════════════════════════════════════════════════════════════
def get_chroma_collection():
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def _make_prop_id(doc_id: str, prop_index: int, prop_text: str) -> str:
    raw = f"{doc_id}::{prop_index}::{prop_text}"
    return "prop_" + hashlib.md5(raw.encode()).hexdigest()[:16]


def _embed_texts(texts: List[str], max_retries: int = 5) -> List[List[float]]:
    """
    Sinh vector embeddings cho danh sach propositions bang Google Gemini API.
    Toi uu:
      - Batch embedding (truyen toan bo texts trong 1 API request duy nhat).
      - Exponential backoff retry khi cham quota 429 (ResourceExhausted).
    """
    if not texts:
        return []

    delay = 10.0
    for attempt in range(1, max_retries + 1):
        try:
            res = genai.embed_content(
                model=EMBEDDING_MODEL_NAME,
                content=texts,
                task_type="RETRIEVAL_DOCUMENT",
            )
            raw = res["embedding"]
            if len(texts) == 1 and isinstance(raw[0], float):
                return [raw]
            return raw
        except Exception as e:
            err_msg = str(e).lower()
            is_quota = "quota" in err_msg or "429" in err_msg or "resourceexhausted" in err_msg or "rate limit" in err_msg
            if is_quota and attempt < max_retries:
                print(f"     [Gemini Rate Limit] Cham 429 o buoc Embedding. Nghi {delay:.0f}s roi thu lai (Lan {attempt}/{max_retries})...")
                time.sleep(delay)
                delay *= 1.5
            else:
                raise e


def index_propositions_to_chroma(collection, chunk: ParentChunk, verbose: bool = False):
    """
    Embed tung proposition va upsert vao ChromaDB.

    Schema ChromaDB:
      document = proposition text          <- embed cai nay de search
      metadata = {
        "doc_id":      UUID cua parent chunk trong DocStore,
        "category":    danh muc tai lieu,
        "section":     heading ## cua doan,
        "source_file": ten file .md goc,
        "prop_index":  vi tri cua proposition trong chunk,
        "question":    section text (tuong thich Java SourceDto / Layer 4),
      }
    """
    propositions = chunk.propositions
    if not propositions:
        return

    for batch_start in range(0, len(propositions), PROPOSITION_BATCH_SIZE):
        batch = propositions[batch_start: batch_start + PROPOSITION_BATCH_SIZE]
        ids, docs, metas = [], [], []

        for i, prop_text in enumerate(batch):
            global_idx = batch_start + i
            ids.append(_make_prop_id(chunk.doc_id, global_idx, prop_text))
            docs.append(prop_text)
            metas.append({
                "doc_id":      chunk.doc_id,
                "category":    chunk.category,
                "section":     chunk.section,
                "source_file": chunk.source_file,
                "prop_index":  global_idx,
                "question":    chunk.section.lstrip("# ").strip(),
            })

        try:
            embeddings = _embed_texts(docs)
        except Exception as e:
            print(f"     [Indexer] Loi embed batch sau khi da retry: {e}. Bo qua batch nay.")
            time.sleep(2)
            continue

        collection.upsert(ids=ids, embeddings=embeddings, documents=docs, metadatas=metas)

        if verbose:
            for pid, ptxt in zip(ids, docs):
                print(f"       + [{pid}] {ptxt[:80]}")

        if batch_start + PROPOSITION_BATCH_SIZE < len(propositions):
            time.sleep(1.0)


# ====================================================================
# Pipeline chinh
# ====================================================================
def run_pipeline(
    docs_dir: Path = DOCS_DIR,
    clear: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Chay toan bo Proposition Indexing pipeline:
      Parse -> Decompose -> Save DocStore -> Embed ChromaDB

    Args:
        docs_dir:  Thu muc chua file .md
        clear:     Xoa sach ChromaDB va DocStore truoc khi ingest
        dry_run:   Chi in propositions, KHONG luu vao storage
        verbose:   In chi tiet tung proposition
    """
    print("\n" + "=" * 70)
    print("PROPOSITION INDEXING PIPELINE")
    print("=" * 70)

    docstore_dir = get_docstore_dir()
    collection = None if dry_run else get_chroma_collection()

    if clear and not dry_run:
        print("\n[CLEAR] Dang xoa sach du lieu cu...")
        clear_docstore(docstore_dir)
        if CHROMA_DB_DIR.exists():
            import shutil
            try:
                shutil.rmtree(CHROMA_DB_DIR)
                print(f"[ChromaDB] Da don sach thu muc '{CHROMA_DB_DIR}'")
            except Exception:
                pass
        CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

    print(f"\n[Buoc 1] Parse documents tu: {docs_dir}")
    chunks = parse_documents(docs_dir)
    print(f"  -> Tim thay {len(chunks)} parent chunks")

    stats = {
        "total_chunks": len(chunks),
        "total_propositions": 0,
        "indexed_chunks": 0,
        "skipped_chunks": 0,
    }

    seen_doc_ids = set()

    print(f"\n[Buoc 2+3] Decompose -> Embed -> Index ({len(chunks)} chunks)...")
    for idx, chunk in enumerate(chunks, 1):
        print(f"\n  [{idx}/{len(chunks)}] {chunk.source_file} | {chunk.section[:50]}")
        if verbose:
            print(f"     Parent ({len(chunk.content.split())} tu): {chunk.content[:100]}...")

        if chunk.doc_id in seen_doc_ids:
            print(f"     [SKIP] Chunk trung noi dung voi chunk da xu ly (doc_id: {chunk.doc_id})")
            stats["skipped_chunks"] += 1
            continue
        seen_doc_ids.add(chunk.doc_id)

        # Resume Checkpoint: Neu khong dung --clear, kiem tra da co trong storage chua de tranh phi quota
        if not clear and not dry_run and (docstore_dir / f"{chunk.doc_id}.json").exists():
            try:
                existing = collection.get(where={"doc_id": chunk.doc_id}, limit=1)
                if existing and existing.get("ids"):
                    print(f"     [RESUME] Chunk da duoc index truoc do ({len(existing['ids'])} vectors). Bo qua de tiet kiem quota.")
                    stats["indexed_chunks"] += 1
                    continue
            except Exception:
                pass

        propositions = decompose_to_propositions(chunk, verbose=verbose)
        chunk.propositions = propositions

        if not propositions:
            print("     WARNING: Khong sinh duoc propositions, bo qua.")
            stats["skipped_chunks"] += 1
            continue

        stats["total_propositions"] += len(propositions)
        stats["indexed_chunks"] += 1

        if dry_run:
            print(f"     [DRY-RUN] {len(propositions)} propositions:")
            for i, p in enumerate(propositions, 1):
                print(f"       {i}. {p}")
            continue

        save_to_docstore(chunk.doc_id, chunk.content, docstore_dir)
        index_propositions_to_chroma(collection, chunk, verbose=verbose)
        # Nghi 2.5s giua cac chunk de luon duoi nguong 15 RPM cua Gemini Free Tier
        time.sleep(2.5)

    print("\n" + "=" * 70)
    print("HOAN TAT")
    print(f"  Parent chunks xu ly : {stats['indexed_chunks']}/{stats['total_chunks']}")
    print(f"  Tong propositions   : {stats['total_propositions']}")
    print(f"  Chunks bo qua       : {stats['skipped_chunks']}")
    if not dry_run and collection is not None:
        print(f"  Vectors trong Chroma: {collection.count()}")
    print("=" * 70)

    return stats


if __name__ == "__main__":
    run_pipeline(verbose=True)
