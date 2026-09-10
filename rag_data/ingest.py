"""
ingest.py — CLI entry-point cho Proposition Indexing Pipeline

Cach chay:
  # Ingest day du (xoa sach va ingest lai)
  python rag_data/ingest.py --clear --verbose

  # Chi xem propositions, khong luu vao storage
  python rag_data/ingest.py --dry-run --verbose

  # Ingest them vao collection hien co (khong xoa)
  python rag_data/ingest.py --verbose
"""

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from proposition_indexer import run_pipeline, DOCS_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Proposition Indexing Pipeline cho ChatMessageE2E RAG"
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DOCS_DIR,
        help=f"Thu muc chua cac file .md (mac dinh: {DOCS_DIR})",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Xoa sach ChromaDB va DocStore truoc khi ingest lai",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chi sinh va in propositions, KHONG luu vao storage",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="In chi tiet tung proposition duoc sinh ra",
    )

    args = parser.parse_args()

    stats = run_pipeline(
        docs_dir=args.docs_dir,
        clear=args.clear,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    if stats["skipped_chunks"] > 0:
        print(f"\nCANH BAO: {stats['skipped_chunks']} chunk bi bo qua do loi Gemini hoac noi dung qua ngan.")

    sys.exit(0)


if __name__ == "__main__":
    main()
