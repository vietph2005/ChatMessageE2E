"""
chat_cli.py — Giao diện Terminal tương tác trực tiếp để test RAG
==============================================================
Chạy lệnh:
    python rag_data/chat_cli.py

Bạn có thể gõ câu hỏi bất kỳ để xem hệ thống 5 Layers hoạt động và trả lời kèm nguồn dẫn.
Gõ 'exit' hoặc 'quit' để thoát.
"""

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Đảm bảo UTF-8 trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from main import run_rag_pipeline


def main():
    print("=" * 65)
    print("🤖 CHATMESSAG E2E — TRÌNH TEST RAG TƯƠNG TÁC (CLI)")
    print("=" * 65)
    print("💡 Mẹo câu hỏi mẫu:")
    print("   1. Làm sao để đăng nhập bằng Google?")
    print("   2. Mã hóa tin nhắn E2EE dùng thuật toán gì?")
    print("   3. Khi mất mạng thì tin nhắn có bị mất không?")
    print("   4. Re-handshake là gì?")
    show_logs = True
    print("💡 Gõ '/log' để bật/tắt hiển thị luồng log chi tiết (Mặc định: BẬT)")
    print("-" * 65)

    while True:
        try:
            user_input = input("\n👤 Bạn: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\n👋 Tạm biệt!")
                break
            if user_input.lower() == "/log":
                show_logs = not show_logs
                status_text = "BẬT" if show_logs else "TẮT"
                print(f"⚙️ [Cài đặt] Hiển thị log chi tiết: {status_text}")
                continue

            if not show_logs:
                print("\n⏳ Đang suy luận qua 5 tầng RAG...")
            result = run_rag_pipeline(user_input, verbose=show_logs)

            print("\n" + "─" * 60)
            print(f"🤖 Bot trả lời:\n{result['answer']}")
            print("─" * 60)


            sources = result.get("sources", [])
            if sources:
                print("📚 Nguồn trích dẫn (Sources):")
                for idx, s in enumerate(sources, 1):
                    category = s.get("category", "")
                    question = s.get("question", "")
                    sim = s.get("similarity", 0.0)
                    print(f"   [{idx}] {question} (Chủ đề: {category} | Sim: {sim})")

        except (KeyboardInterrupt, EOFError):
            print("\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"\n❌ Có lỗi xảy ra: {e}")


if __name__ == "__main__":
    main()
