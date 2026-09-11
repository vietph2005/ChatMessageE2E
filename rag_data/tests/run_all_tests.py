"""
run_all_tests.py — Trình Chạy Toàn Bộ Test Suite Cho RAG Pipeline (Layers 1, 2, 3, 4, 5)
========================================================================================
Tập trung toàn bộ test suite vào một điểm thực thi duy nhất:
  - Layer 1: Intent Classifier (Small talk vs App question)
  - Layer 2: Query Rewriter (RAG Fusion & Multi-Query Generation)
  - Layer 3: CRAG Retriever (Reciprocal Rank Fusion & Document Grader)
  - Layer 4: Generator (Grounded Prompting & Sources DTO)
  - Layer 5: Verifier (Self-RAG: Hallucination Grader, Usefulness & Self-Correction)
  - Hỗ trợ cờ --layer 1|2|3|4|5 để chạy lẻ từng layer
  - Hỗ trợ cờ --live để chạy benchmark thực tế
"""

import sys
import unittest
import argparse
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
RAG_DATA_DIR = CURRENT_DIR.parent
if str(RAG_DATA_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_DATA_DIR))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from test_layer1 import TestLayer1Unit
from test_layer2 import TestLayer2Unit
from test_layer3 import TestLayer3Unit
from test_layer4 import TestLayer4Unit
from test_layer5 import TestLayer5Unit


def run_unit_tests(layers=None):
    """Chạy toàn bộ Unit Tests đã được mock của các layer."""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    layers_to_run = layers or [1, 2, 3, 4, 5]

    print("\n" + "=" * 80)
    print(f"🧪 CHẠY TOÀN BỘ UNIT TESTS CHO RAG PIPELINE (LAYERS: {layers_to_run})")
    print("   (Môi trường cô lập, 100% Mock, 0ms latency, không tốn quota API)")
    print("=" * 80 + "\n")

    if 1 in layers_to_run:
        suite.addTests(loader.loadTestsFromTestCase(TestLayer1Unit))
    if 2 in layers_to_run:
        suite.addTests(loader.loadTestsFromTestCase(TestLayer2Unit))
    if 3 in layers_to_run:
        suite.addTests(loader.loadTestsFromTestCase(TestLayer3Unit))
    if 4 in layers_to_run:
        suite.addTests(loader.loadTestsFromTestCase(TestLayer4Unit))
    if 5 in layers_to_run:
        suite.addTests(loader.loadTestsFromTestCase(TestLayer5Unit))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description="Trình chạy kiểm thử tập trung cho toàn bộ ChatMessageE2E RAG Pipeline")
    parser.add_argument("--layer", type=int, choices=[1, 2, 3, 4, 5], help="Chỉ chạy layer cụ thể (1, 2, 3, 4 hoặc 5)")
    parser.add_argument("--live", action="store_true", help="Chạy Live Benchmark trên layer được chỉ định (hoặc tất cả)")
    args = parser.parse_args()

    selected_layers = [args.layer] if args.layer else [1, 2, 3, 4, 5]

    if not args.live:
        success = run_unit_tests(selected_layers)
        sys.exit(0 if success else 1)
    else:
        print("\n🌐 CHẾ ĐỘ LIVE BENCHMARK...")
        if 1 in selected_layers:
            from test_layer1 import run_live_benchmark as live_l1
            live_l1()
        if 2 in selected_layers:
            from test_layer2 import run_live_benchmark as live_l2
            live_l2()
        if 3 in selected_layers:
            from test_layer3 import run_live_benchmark as live_l3
            live_l3()
        if 4 in selected_layers:
            from test_layer4 import run_live_benchmark as live_l4
            live_l4()
        if 5 in selected_layers:
            from test_layer5 import run_live_benchmark as live_l5
            live_l5()


if __name__ == "__main__":
    main()
